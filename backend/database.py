from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from pymongo import MongoClient, DESCENDING
from pymongo.collection import Collection
from bson import ObjectId
import os
import numpy as np
from models import UserDB, SiteDB, InteractionDB, AnalyticsStats, DashboardStats
from auth import get_password_hash, verify_password, create_reset_token
import logging

logger = logging.getLogger(__name__)

class DatabaseService:
    def __init__(self, mongo_client: MongoClient):
        self.db = mongo_client.ai_voice_assistant
        self.users: Collection = self.db.users
        self.sites: Collection = self.db.sites
        self.interactions: Collection = self.db.interactions
        self.conversations: Collection = self.db.conversations
        
        # New collections for Website Intelligence
        self.site_intelligence: Collection = self.db.site_intelligence
        self.user_journeys: Collection = self.db.user_journeys
        self.intent_analysis: Collection = self.db.intent_analysis
        self.navigation_suggestions: Collection = self.db.navigation_suggestions
        self.roi_reports: Collection = self.db.roi_reports
        
        # Create indexes for performance
        self._create_indexes()
    
    def _create_indexes(self):
        """Create database indexes for performance."""
        try:
            # Users indexes
            self.users.create_index("email", unique=True)
            self.users.create_index("reset_token")
            
            # Sites indexes
            self.sites.create_index("user_id")
            self.sites.create_index("domain")
            self.sites.create_index([("user_id", 1), ("is_active", 1)])
            
            # Interactions indexes
            self.interactions.create_index("site_id")
            self.interactions.create_index("session_id")
            self.interactions.create_index("timestamp")
            self.interactions.create_index([("site_id", 1), ("timestamp", -1)])
            
            # Conversations indexes
            self.conversations.create_index("site_id")
            self.conversations.create_index("session_id")
            self.conversations.create_index("timestamp")
            
            # Website Intelligence indexes
            self.site_intelligence.create_index("site_id", unique=True)
            self.site_intelligence.create_index("domain")
            self.site_intelligence.create_index("last_crawl")
            
            # User Journeys indexes
            self.user_journeys.create_index("visitor_id")
            self.user_journeys.create_index("session_id")
            self.user_journeys.create_index("site_id")
            self.user_journeys.create_index([("site_id", 1), ("timestamp", -1)])
            
            # Intent Analysis indexes
            self.intent_analysis.create_index("site_id")
            self.intent_analysis.create_index("intent_type")
            self.intent_analysis.create_index("timestamp")
            
            # Navigation Suggestions indexes
            self.navigation_suggestions.create_index("site_id")
            self.navigation_suggestions.create_index("current_page")
            
            # ROI Reports indexes
            self.roi_reports.create_index("site_id")
            self.roi_reports.create_index([("site_id", 1), ("period_start", -1)])
            
            logger.info("Database indexes created successfully")
        except Exception as e:
            logger.error(f"Error creating indexes: {e}")
    
    # User Operations
    async def create_user(self, email: str, full_name: str, password: str) -> Optional[UserDB]:
        """Create a new user."""
        try:
            # Check if user already exists
            if self.users.find_one({"email": email}):
                return None
            
            user_data = UserDB(
                email=email,
                full_name=full_name,
                hashed_password=get_password_hash(password)
            )
            
            result = self.users.insert_one(user_data.dict())
            if result.inserted_id:
                return user_data
            return None
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return None
    
    async def get_user_by_email(self, email: str) -> Optional[UserDB]:
        """Get user by email."""
        try:
            user_data = self.users.find_one({"email": email})
            if user_data:
                user_data.pop('_id', None)  # Remove MongoDB ObjectId
                return UserDB(**user_data)
            return None
        except Exception as e:
            logger.error(f"Error getting user by email: {e}")
            return None
    
    async def get_user_by_id(self, user_id: str) -> Optional[UserDB]:
        """Get user by ID."""
        try:
            user_data = self.users.find_one({"id": user_id})
            if user_data:
                user_data.pop('_id', None)
                return UserDB(**user_data)
            return None
        except Exception as e:
            logger.error(f"Error getting user by ID: {e}")
            return None
    
    async def authenticate_user(self, email: str, password: str) -> Optional[UserDB]:
        """Authenticate user credentials."""
        try:
            user = await self.get_user_by_email(email)
            if user and verify_password(password, user.hashed_password):
                return user
            return None
        except Exception as e:
            logger.error(f"Error authenticating user: {e}")
            return None
    
    async def update_user(self, user_id: str, update_data: Dict[str, Any]) -> bool:
        """Update user information."""
        try:
            update_data["updated_at"] = datetime.utcnow()
            result = self.users.update_one(
                {"id": user_id},
                {"$set": update_data}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating user: {e}")
            return False
    
    async def set_reset_token(self, email: str) -> Optional[str]:
        """Set password reset token for user."""
        try:
            reset_token = create_reset_token()
            reset_expires = datetime.utcnow() + timedelta(minutes=60)
            
            result = self.users.update_one(
                {"email": email},
                {"$set": {
                    "reset_token": reset_token,
                    "reset_token_expires": reset_expires,
                    "updated_at": datetime.utcnow()
                }}
            )
            
            if result.modified_count > 0:
                return reset_token
            return None
        except Exception as e:
            logger.error(f"Error setting reset token: {e}")
            return None
    
    async def reset_password(self, token: str, new_password: str) -> bool:
        """Reset user password with token."""
        try:
            user_data = self.users.find_one({
                "reset_token": token,
                "reset_token_expires": {"$gt": datetime.utcnow()}
            })
            
            if not user_data:
                return False
            
            result = self.users.update_one(
                {"id": user_data["id"]},
                {"$set": {
                    "hashed_password": get_password_hash(new_password),
                    "reset_token": None,
                    "reset_token_expires": None,
                    "updated_at": datetime.utcnow()
                }}
            )
            
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error resetting password: {e}")
            return False
    
    # Site Operations
    async def create_site(self, user_id: str, site_data: Dict[str, Any]) -> Optional[SiteDB]:
        """Create a new site."""
        try:
            site = SiteDB(
                user_id=user_id,
                **site_data
            )
            
            result = self.sites.insert_one(site.dict())
            if result.inserted_id:
                return site
            return None
        except Exception as e:
            logger.error(f"Error creating site: {e}")
            return None
    
    async def get_user_sites(self, user_id: str) -> List[SiteDB]:
        """Get all sites for a user."""
        try:
            sites_data = list(self.sites.find({"user_id": user_id}).sort("created_at", DESCENDING))
            sites = []
            for site_data in sites_data:
                site_data.pop('_id', None)
                sites.append(SiteDB(**site_data))
            return sites
        except Exception as e:
            logger.error(f"Error getting user sites: {e}")
            return []
    
    async def get_site_by_id(self, site_id: str, user_id: str) -> Optional[SiteDB]:
        """Get site by ID and user ID."""
        try:
            site_data = self.sites.find_one({"id": site_id, "user_id": user_id})
            if site_data:
                site_data.pop('_id', None)
                return SiteDB(**site_data)
            return None
        except Exception as e:
            logger.error(f"Error getting site by ID: {e}")
            return None
    
    async def get_site_by_domain(self, domain: str) -> Optional[SiteDB]:
        """Get site by domain."""
        try:
            site_data = self.sites.find_one({"domain": domain, "is_active": True})
            if site_data:
                site_data.pop('_id', None)
                return SiteDB(**site_data)
            return None
        except Exception as e:
            logger.error(f"Error getting site by domain: {e}")
            return None
    
    async def update_site(self, site_id: str, user_id: str, update_data: Dict[str, Any]) -> bool:
        """Update site information."""
        try:
            update_data["updated_at"] = datetime.utcnow()
            result = self.sites.update_one(
                {"id": site_id, "user_id": user_id},
                {"$set": update_data}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating site: {e}")
            return False
    
    async def delete_site(self, site_id: str, user_id: str) -> bool:
        """Delete site (soft delete)."""
        try:
            result = self.sites.update_one(
                {"id": site_id, "user_id": user_id},
                {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error deleting site: {e}")
            return False
    
    # Analytics Operations
    async def create_interaction(self, interaction_data: Dict[str, Any]) -> bool:
        """Create a new interaction record."""
        try:
            interaction = InteractionDB(**interaction_data)
            result = self.interactions.insert_one(interaction.dict())
            return bool(result.inserted_id)
        except Exception as e:
            logger.error(f"Error creating interaction: {e}")
            return False
    
    async def get_site_analytics(self, site_id: str, days: int = 30) -> AnalyticsStats:
        """Get analytics for a site."""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Total interactions
            total_interactions = self.interactions.count_documents({
                "site_id": site_id,
                "timestamp": {"$gte": start_date}
            })
            
            # Total sessions
            total_sessions = len(self.interactions.distinct("session_id", {
                "site_id": site_id,
                "timestamp": {"$gte": start_date}
            }))
            
            # Total conversations
            total_conversations = self.conversations.count_documents({
                "site_id": site_id,
                "timestamp": {"$gte": start_date}
            })
            
            # Average session duration (simplified)
            avg_session_duration = 0.0  # TODO: Implement proper session duration calculation
            
            # Top interaction types
            pipeline = [
                {"$match": {"site_id": site_id, "timestamp": {"$gte": start_date}}},
                {"$group": {"_id": "$interaction_type", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
                {"$limit": 10}
            ]
            top_types = list(self.interactions.aggregate(pipeline))
            top_interaction_types = [{"type": item["_id"], "count": item["count"]} for item in top_types]
            
            # Daily stats
            daily_pipeline = [
                {"$match": {"site_id": site_id, "timestamp": {"$gte": start_date}}},
                {"$group": {
                    "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$timestamp"}},
                    "interactions": {"$sum": 1},
                    "sessions": {"$addToSet": "$session_id"}
                }},
                {"$project": {
                    "date": "$_id",
                    "interactions": 1,
                    "sessions": {"$size": "$sessions"}
                }},
                {"$sort": {"date": 1}}
            ]
            daily_data = list(self.interactions.aggregate(daily_pipeline))
            daily_stats = [{"date": item["date"], "interactions": item["interactions"], "sessions": item["sessions"]} for item in daily_data]
            
            # Popular questions
            popular_pipeline = [
                {"$match": {"site_id": site_id, "user_message": {"$exists": True, "$ne": None}, "timestamp": {"$gte": start_date}}},
                {"$group": {"_id": "$user_message", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
                {"$limit": 10}
            ]
            popular_data = list(self.interactions.aggregate(popular_pipeline))
            popular_questions = [{"question": item["_id"], "count": item["count"]} for item in popular_data]
            
            return AnalyticsStats(
                total_interactions=total_interactions,
                total_sessions=total_sessions,
                total_conversations=total_conversations,
                avg_session_duration=avg_session_duration,
                top_interaction_types=top_interaction_types,
                daily_stats=daily_stats,
                popular_questions=popular_questions
            )
        except Exception as e:
            logger.error(f"Error getting site analytics: {e}")
            return AnalyticsStats(
                total_interactions=0,
                total_sessions=0,
                total_conversations=0,
                avg_session_duration=0.0,
                top_interaction_types=[],
                daily_stats=[],
                popular_questions=[]
            )
    
    async def get_dashboard_stats(self, user_id: str) -> DashboardStats:
        """Get dashboard statistics for a user."""
        try:
            # Get user's sites
            user_site_ids = [site["id"] for site in self.sites.find({"user_id": user_id, "is_active": True}, {"id": 1})]
            
            # Total sites
            total_sites = len(user_site_ids)
            
            # Total interactions
            total_interactions = self.interactions.count_documents({
                "site_id": {"$in": user_site_ids}
            })
            
            # Total conversations
            total_conversations = self.conversations.count_documents({
                "site_id": {"$in": user_site_ids}
            })
            
            # Active sessions (last 24 hours)
            yesterday = datetime.utcnow() - timedelta(days=1)
            active_sessions = len(self.interactions.distinct("session_id", {
                "site_id": {"$in": user_site_ids},
                "timestamp": {"$gte": yesterday}
            }))
            
            # Recent interactions
            recent_data = list(self.interactions.find({
                "site_id": {"$in": user_site_ids}
            }).sort("timestamp", DESCENDING).limit(10))
            
            recent_interactions = []
            for interaction in recent_data:
                interaction.pop('_id', None)
                recent_interactions.append(InteractionDB(**interaction))
            
            # Site performance
            site_performance = []
            for site_id in user_site_ids:
                site_interactions = self.interactions.count_documents({"site_id": site_id})
                site_data = self.sites.find_one({"id": site_id}, {"name": 1})
                if site_data:
                    site_performance.append({
                        "site_id": site_id,
                        "site_name": site_data["name"],
                        "interactions": site_interactions
                    })
            
            # Sort by interactions
            site_performance.sort(key=lambda x: x["interactions"], reverse=True)
            
            return DashboardStats(
                total_sites=total_sites,
                total_interactions=total_interactions,
                total_conversations=total_conversations,
                active_sessions=active_sessions,
                recent_interactions=recent_interactions,
                site_performance=site_performance
            )
        except Exception as e:
            logger.error(f"Error getting dashboard stats: {e}")
            return DashboardStats(
                total_sites=0,
                total_interactions=0,
                total_conversations=0,
                active_sessions=0,
                recent_interactions=[],
                site_performance=[]
            )
    
    # Utility methods
    async def get_site_config(self, site_id: str) -> Optional[Dict[str, Any]]:
        """Get site configuration for widget."""
        try:
            site_data = self.sites.find_one({"id": site_id, "is_active": True})
            if site_data:
                return {
                    "site_id": site_data["id"],
                    "greeting_message": site_data["greeting_message"],
                    "bot_name": site_data["bot_name"],
                    "theme": site_data["theme"],
                    "position": site_data["position"],
                    "auto_greet": site_data["auto_greet"],
                    "voice_enabled": site_data["voice_enabled"],
                    "language": site_data["language"]
                }
            return None
        except Exception as e:
            logger.error(f"Error getting site config: {e}")
            return None
    
    # Website Intelligence Methods
    async def store_site_structure(self, structure_data: Dict[str, Any]) -> bool:
        """Store website intelligence data."""
        try:
            # Update or insert site intelligence
            result = self.site_intelligence.update_one(
                {"site_id": structure_data.get("site_id", structure_data["domain"])},
                {"$set": structure_data},
                upsert=True
            )
            return bool(result.upserted_id or result.modified_count)
        except Exception as e:
            logger.error(f"Error storing site structure: {e}")
            return False
    
    async def get_site_intelligence(self, site_id: str) -> Optional[Dict[str, Any]]:
        """Get website intelligence data for a site."""
        try:
            intelligence_data = self.site_intelligence.find_one({"site_id": site_id})
            if intelligence_data:
                intelligence_data.pop('_id', None)
                return intelligence_data
            return None
        except Exception as e:
            logger.error(f"Error getting site intelligence: {e}")
            return None
    
    async def store_user_journey(self, journey_data: Dict[str, Any]) -> bool:
        """Store user journey data."""
        try:
            result = self.user_journeys.insert_one(journey_data)
            return bool(result.inserted_id)
        except Exception as e:
            logger.error(f"Error storing user journey: {e}")
            return False
    
    async def get_user_journeys(self, site_id: str, visitor_id: Optional[str] = None, days: int = 30) -> List[Dict[str, Any]]:
        """Get user journeys for analysis."""
        try:
            query = {"site_id": site_id}
            if visitor_id:
                query["visitor_id"] = visitor_id
            
            start_date = datetime.utcnow() - timedelta(days=days)
            query["timestamp"] = {"$gte": start_date}
            
            journeys = list(self.user_journeys.find(query).sort("timestamp", DESCENDING).limit(100))
            
            # Remove MongoDB ObjectIds
            for journey in journeys:
                journey.pop('_id', None)
            
            return journeys
        except Exception as e:
            logger.error(f"Error getting user journeys: {e}")
            return []
    
    async def store_intent_analysis(self, intent_data: Dict[str, Any]) -> bool:
        """Store intent analysis data."""
        try:
            result = self.intent_analysis.insert_one(intent_data)
            return bool(result.inserted_id)
        except Exception as e:
            logger.error(f"Error storing intent analysis: {e}")
            return False
    
    async def get_intent_analytics(self, site_id: str, days: int = 30) -> Dict[str, Any]:
        """Get intent analytics for ROI reporting."""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Get intent distribution
            intent_pipeline = [
                {"$match": {"site_id": site_id, "timestamp": {"$gte": start_date}}},
                {"$group": {
                    "_id": "$intent_type",
                    "count": {"$sum": 1},
                    "avg_confidence": {"$avg": "$confidence"},
                    "avg_conversion_prob": {"$avg": "$conversion_probability"}
                }},
                {"$sort": {"count": -1}}
            ]
            
            intent_distribution = list(self.intent_analysis.aggregate(intent_pipeline))
            
            # Get journey stage distribution
            journey_pipeline = [
                {"$match": {"site_id": site_id, "timestamp": {"$gte": start_date}}},
                {"$group": {
                    "_id": "$journey_stage",
                    "count": {"$sum": 1}
                }},
                {"$sort": {"count": -1}}
            ]
            
            journey_distribution = list(self.intent_analysis.aggregate(journey_pipeline))
            
            # Calculate average confidence and conversion probability
            avg_stats = list(self.intent_analysis.aggregate([
                {"$match": {"site_id": site_id, "timestamp": {"$gte": start_date}}},
                {"$group": {
                    "_id": None,
                    "avg_confidence": {"$avg": "$confidence"},
                    "avg_conversion_prob": {"$avg": "$conversion_probability"},
                    "total_queries": {"$sum": 1}
                }}
            ]))
            
            avg_confidence = avg_stats[0]["avg_confidence"] if avg_stats else 0
            avg_conversion_prob = avg_stats[0]["avg_conversion_prob"] if avg_stats else 0
            total_queries = avg_stats[0]["total_queries"] if avg_stats else 0
            
            return {
                "intent_distribution": [{"intent": item["_id"], "count": item["count"], 
                                       "avg_confidence": item["avg_confidence"],
                                       "avg_conversion_prob": item["avg_conversion_prob"]} 
                                      for item in intent_distribution],
                "journey_distribution": [{"stage": item["_id"], "count": item["count"]} 
                                       for item in journey_distribution],
                "overall_metrics": {
                    "total_queries_analyzed": total_queries,
                    "average_confidence": avg_confidence,
                    "average_conversion_probability": avg_conversion_prob
                }
            }
        except Exception as e:
            logger.error(f"Error getting intent analytics: {e}")
            return {}
    
    async def store_navigation_suggestion(self, suggestion_data: Dict[str, Any]) -> bool:
        """Store navigation suggestion data."""
        try:
            result = self.navigation_suggestions.insert_one(suggestion_data)
            return bool(result.inserted_id)
        except Exception as e:
            logger.error(f"Error storing navigation suggestion: {e}")
            return False
    
    async def get_navigation_analytics(self, site_id: str, days: int = 30) -> Dict[str, Any]:
        """Get navigation analytics."""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Get most requested pages/queries
            popular_queries = list(self.navigation_suggestions.aggregate([
                {"$match": {"site_id": site_id, "timestamp": {"$gte": start_date}}},
                {"$group": {"_id": "$query", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
                {"$limit": 10}
            ]))
            
            # Get success rate of suggestions
            success_pipeline = [
                {"$match": {"site_id": site_id, "timestamp": {"$gte": start_date}}},
                {"$group": {
                    "_id": None,
                    "avg_success_prob": {"$avg": "$success_probability"},
                    "total_suggestions": {"$sum": 1}
                }}
            ]
            
            success_stats = list(self.navigation_suggestions.aggregate(success_pipeline))
            avg_success_prob = success_stats[0]["avg_success_prob"] if success_stats else 0
            total_suggestions = success_stats[0]["total_suggestions"] if success_stats else 0
            
            return {
                "popular_queries": [{"query": item["_id"], "count": item["count"]} 
                                  for item in popular_queries],
                "navigation_metrics": {
                    "total_navigation_requests": total_suggestions,
                    "average_success_probability": avg_success_prob
                }
            }
        except Exception as e:
            logger.error(f"Error getting navigation analytics: {e}")
            return {}
    
    async def generate_roi_report(self, site_id: str, days: int = 30) -> Dict[str, Any]:
        """Generate comprehensive ROI report."""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Get basic site metrics
            site_analytics = await self.get_site_analytics(site_id, days)
            
            # Get AI-specific metrics
            ai_interactions = self.interactions.count_documents({
                "site_id": site_id,
                "interaction_type": {"$in": ["ai_response", "voice_input", "text_input"]},
                "timestamp": {"$gte": start_date}
            })
            
            # Get user journey metrics
            journeys = await self.get_user_journeys(site_id, days=days)
            
            # Calculate conversion metrics
            total_conversions = sum(1 for journey in journeys if journey.get("converted", False))
            conversion_rate = (total_conversions / len(journeys)) * 100 if journeys else 0
            
            # Get intent analytics
            intent_analytics = await self.get_intent_analytics(site_id, days)
            
            # Get navigation analytics
            nav_analytics = await self.get_navigation_analytics(site_id, days)
            
            # Calculate user satisfaction (based on conversation completion and positive responses)
            satisfaction_pipeline = [
                {"$match": {"site_id": site_id, "timestamp": {"$gte": start_date}}},
                {"$group": {
                    "_id": None,
                    "total_interactions": {"$sum": 1},
                    "completed_conversations": {"$sum": {"$cond": [{"$gt": ["$conversation_length", 3]}, 1, 0]}}
                }}
            ]
            
            satisfaction_stats = list(self.conversations.aggregate(satisfaction_pipeline))
            if satisfaction_stats:
                completion_rate = (satisfaction_stats[0]["completed_conversations"] / 
                                 satisfaction_stats[0]["total_interactions"]) * 100
                user_satisfaction = min(100, completion_rate * 1.2)  # Adjusted satisfaction score
            else:
                user_satisfaction = 0
            
            # Calculate estimated cost savings
            support_cost_per_ticket = 25  # Estimated cost per support ticket
            estimated_tickets_prevented = ai_interactions * 0.3  # 30% of AI interactions prevent support tickets
            support_cost_savings = estimated_tickets_prevented * support_cost_per_ticket
            
            # Calculate navigation efficiency
            avg_pages_per_session = np.mean([len(journey.get("pages_visited", [])) for journey in journeys]) if journeys else 0
            navigation_efficiency = min(100, (avg_pages_per_session / 5) * 100)  # Optimal is 5 pages per session
            
            roi_report = {
                "site_id": site_id,
                "period_start": start_date.isoformat(),
                "period_end": datetime.utcnow().isoformat(),
                "generated_at": datetime.utcnow().isoformat(),
                
                # Engagement Metrics
                "engagement_metrics": {
                    "total_visitors": len(set([journey.get("visitor_id") for journey in journeys])),
                    "total_page_views": sum([len(journey.get("pages_visited", [])) for journey in journeys]),
                    "total_sessions": site_analytics.total_sessions,
                    "avg_session_duration": site_analytics.avg_session_duration,
                    "pages_per_session": avg_pages_per_session
                },
                
                # Conversion Metrics
                "conversion_metrics": {
                    "total_conversions": total_conversions,
                    "conversion_rate": conversion_rate,
                    "ai_interactions": ai_interactions,
                    "intent_accuracy": intent_analytics.get("overall_metrics", {}).get("average_confidence", 0) * 100
                },
                
                # ROI Metrics
                "roi_metrics": {
                    "support_cost_savings": support_cost_savings,
                    "estimated_tickets_prevented": estimated_tickets_prevented,
                    "user_satisfaction_score": user_satisfaction,
                    "navigation_efficiency": navigation_efficiency,
                    "ai_resolution_rate": min(100, (ai_interactions / site_analytics.total_interactions) * 100) if site_analytics.total_interactions > 0 else 0
                },
                
                # Detailed Analytics
                "intent_analytics": intent_analytics,
                "navigation_analytics": nav_analytics,
                "user_journey_insights": {
                    "total_journeys": len(journeys),
                    "completed_journeys": total_conversions,
                    "avg_journey_length": avg_pages_per_session,
                    "bounce_rate": max(0, 100 - (avg_pages_per_session / 3) * 100)
                }
            }
            
            # Store the report
            await self.store_roi_report(roi_report)
            
            return roi_report
            
        except Exception as e:
            logger.error(f"Error generating ROI report: {e}")
            return {}
    
    async def store_roi_report(self, report_data: Dict[str, Any]) -> bool:
        """Store ROI report."""
        try:
            result = self.roi_reports.insert_one(report_data)
            return bool(result.inserted_id)
        except Exception as e:
            logger.error(f"Error storing ROI report: {e}")
            return False
    
    async def get_latest_roi_report(self, site_id: str) -> Optional[Dict[str, Any]]:
        """Get the latest ROI report for a site."""
        try:
            report = self.roi_reports.find_one(
                {"site_id": site_id},
                sort=[("generated_at", DESCENDING)]
            )
            if report:
                report.pop('_id', None)
                return report
            return None
        except Exception as e:
            logger.error(f"Error getting latest ROI report: {e}")
            return None