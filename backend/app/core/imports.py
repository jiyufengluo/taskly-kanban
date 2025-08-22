# 确保所有必要的导入都存在
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

# FastAPI imports
from fastapi import FastAPI, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.routing import APIRouter

# SQLAlchemy imports
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, ForeignKey, Table, Boolean, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship

# Pydantic imports
from pydantic import BaseModel, EmailStr

# Security imports
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import timedelta

# Redis imports
import redis

# Core settings
from pydantic_settings import BaseSettings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)