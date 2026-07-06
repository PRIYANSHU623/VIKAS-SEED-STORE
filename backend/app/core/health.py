"""
Health Check and Monitoring Endpoints
Provides comprehensive system health status
"""

from datetime import datetime
from typing import Dict, Any
import psutil
import logging

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.database.db import SessionLocal
from app.core.config import ENVIRONMENT, GEMINI_API_KEY

logger = logging.getLogger(__name__)


class HealthChecker:
    """Provides health check information for various components"""
    
    @staticmethod
    async def get_database_health() -> Dict[str, Any]:
        """Check database connectivity and basic health"""
        try:
            db = SessionLocal()
            db.execute(text("SELECT 1"))
            db.close()
            return {
                "status": "healthy",
                "type": "PostgreSQL",
                "message": "Database connection successful"
            }
        except SQLAlchemyError as e:
            logger.error(f"Database health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "type": "PostgreSQL",
                "message": f"Database connection failed: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Unexpected error in database health check: {str(e)}")
            return {
                "status": "unhealthy",
                "type": "PostgreSQL",
                "message": f"Unexpected error: {str(e)}"
            }
    
    @staticmethod
    def get_system_health() -> Dict[str, Any]:
        """Check system resources (CPU, Memory, Disk)"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Determine health status based on thresholds
            status = "healthy"
            if cpu_percent > 90 or memory.percent > 90 or disk.percent > 90:
                status = "degraded"
            if cpu_percent > 95 or memory.percent > 95 or disk.percent > 95:
                status = "unhealthy"
            
            return {
                "status": status,
                "cpu": {
                    "percent": cpu_percent,
                    "threshold": "90%"
                },
                "memory": {
                    "percent": memory.percent,
                    "available_mb": memory.available / (1024 * 1024),
                    "total_mb": memory.total / (1024 * 1024),
                    "threshold": "90%"
                },
                "disk": {
                    "percent": disk.percent,
                    "free_gb": disk.free / (1024 * 1024 * 1024),
                    "total_gb": disk.total / (1024 * 1024 * 1024),
                    "threshold": "90%"
                }
            }
        except Exception as e:
            logger.error(f"System health check failed: {str(e)}")
            return {
                "status": "unknown",
                "message": f"Failed to get system metrics: {str(e)}"
            }
    
    @staticmethod
    def get_ai_service_health() -> Dict[str, Any]:
        """Check AI service availability (Gemini API)"""
        # This is a simple check - in production, you might want to make an actual API call
        if GEMINI_API_KEY and GEMINI_API_KEY != "test-gemini-api-key":
            return {
                "status": "healthy",
                "service": "Gemini API",
                "message": "API key configured"
            }
        else:
            return {
                "status": "degraded",
                "service": "Gemini API",
                "message": "API key not configured or invalid"
            }
    
    @staticmethod
    def get_storage_health() -> Dict[str, Any]:
        """Check uploads directory status"""
        try:
            from pathlib import Path
            upload_dir = Path("app/uploads")
            
            if not upload_dir.exists():
                return {
                    "status": "unhealthy",
                    "message": "Uploads directory does not exist"
                }
            
            # Check if writable
            test_file = upload_dir / ".health_check"
            test_file.touch()
            test_file.unlink()
            
            return {
                "status": "healthy",
                "message": "Uploads directory accessible and writable"
            }
        except Exception as e:
            logger.error(f"Storage health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "message": f"Storage check failed: {str(e)}"
            }
    
    @classmethod
    async def get_full_health(cls) -> Dict[str, Any]:
        """Get comprehensive health status"""
        db_health = await cls.get_database_health()
        system_health = cls.get_system_health()
        ai_health = cls.get_ai_service_health()
        storage_health = cls.get_storage_health()
        
        # Determine overall status
        statuses = [
            db_health.get("status"),
            system_health.get("status"),
            ai_health.get("status"),
            storage_health.get("status")
        ]
        
        if "unhealthy" in statuses:
            overall_status = "unhealthy"
        elif "degraded" in statuses:
            overall_status = "degraded"
        else:
            overall_status = "healthy"
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "environment": ENVIRONMENT,
            "status": overall_status,
            "components": {
                "database": db_health,
                "system": system_health,
                "ai_service": ai_health,
                "storage": storage_health
            }
        }
