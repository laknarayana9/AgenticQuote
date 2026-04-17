"""
SQLite to Postgres Migration Script
Migrates data from SQLite database to Postgres database.
"""

import sqlite3
import psycopg2
from psycopg2.extras import execute_batch
import json
import os
from datetime import datetime
from typing import Dict, Any, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SQLiteToPostgresMigrator:
    """Migrates data from SQLite to Postgres."""
    
    def __init__(self, sqlite_path: str, postgres_config: Dict[str, str]):
        self.sqlite_path = sqlite_path
        self.postgres_config = postgres_config
        self.sqlite_conn = None
        self.postgres_conn = None
    
    def connect(self):
        """Connect to both databases."""
        # Connect to SQLite
        self.sqlite_conn = sqlite3.connect(self.sqlite_path)
        self.sqlite_conn.row_factory = sqlite3.Row
        
        # Connect to Postgres
        self.postgres_conn = psycopg2.connect(**self.postgres_config)
        self.postgres_conn.autocommit = False
        
        logger.info("Connected to SQLite and Postgres")
    
    def close(self):
        """Close database connections."""
        if self.sqlite_conn:
            self.sqlite_conn.close()
        if self.postgres_conn:
            self.postgres_conn.close()
        logger.info("Closed database connections")
    
    def migrate_runs(self):
        """Migrate runs table."""
        logger.info("Migrating runs table...")
        
        sqlite_cursor = self.sqlite_conn.cursor()
        postgres_cursor = self.postgres_conn.cursor()
        
        # Fetch runs from SQLite
        sqlite_cursor.execute("SELECT * FROM runs")
        rows = sqlite_cursor.fetchall()
        
        # Insert into Postgres
        insert_query = """
            INSERT INTO runs (id, run_id, quote_id, status, submission_json, workflow_state_json, created_at, updated_at)
            VALUES (gen_random_uuid(), %s, %s, %s, %s::jsonb, %s::jsonb, %s, %s)
            ON CONFLICT (run_id) DO NOTHING
        """
        
        data = []
        for row in rows:
            row_dict = dict(row)
            data.append((
                row_dict.get('run_id'),
                row_dict.get('quote_id'),
                row_dict.get('status', 'processing'),
                row_dict.get('submission_json'),
                row_dict.get('workflow_state_json'),
                row_dict.get('created_at'),
                row_dict.get('updated_at')
            ))
        
        if data:
            execute_batch(postgres_cursor, insert_query, data)
            self.postgres_conn.commit()
            logger.info(f"Migrated {len(data)} runs")
        else:
            logger.info("No runs to migrate")
    
    def migrate_human_reviews(self):
        """Migrate human_reviews table."""
        logger.info("Migrating human_reviews table...")
        
        sqlite_cursor = self.sqlite_conn.cursor()
        postgres_cursor = self.postgres_conn.cursor()
        
        # Fetch human reviews from SQLite
        sqlite_cursor.execute("SELECT * FROM human_reviews")
        rows = sqlite_cursor.fetchall()
        
        # Insert into Postgres
        insert_query = """
            INSERT INTO human_reviews (id, run_id, status, reviewer_id, review_notes, decision, created_at, completed_at)
            VALUES (gen_random_uuid(), %s, %s, %s, %s, %s, %s, %s)
        """
        
        data = []
        for row in rows:
            row_dict = dict(row)
            data.append((
                row_dict.get('run_id'),
                row_dict.get('status', 'pending'),
                row_dict.get('reviewer_id'),
                row_dict.get('review_notes'),
                row_dict.get('decision'),
                row_dict.get('created_at'),
                row_dict.get('completed_at')
            ))
        
        if data:
            execute_batch(postgres_cursor, insert_query, data)
            self.postgres_conn.commit()
            logger.info(f"Migrated {len(data)} human reviews")
        else:
            logger.info("No human reviews to migrate")
    
    def migrate_quotes(self):
        """Migrate quotes table."""
        logger.info("Migrating quotes table...")
        
        sqlite_cursor = self.sqlite_conn.cursor()
        postgres_cursor = self.postgres_conn.cursor()
        
        # Fetch quotes from SQLite
        sqlite_cursor.execute("SELECT * FROM quotes")
        rows = sqlite_cursor.fetchall()
        
        # Insert into Postgres
        insert_query = """
            INSERT INTO quotes (id, run_id, quote_id, applicant_name, address, coverage_amount, premium_amount, decision, created_at)
            VALUES (gen_random_uuid(), %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        data = []
        for row in rows:
            row_dict = dict(row)
            data.append((
                row_dict.get('run_id'),
                row_dict.get('quote_id'),
                row_dict.get('applicant_name'),
                row_dict.get('address'),
                row_dict.get('coverage_amount'),
                row_dict.get('premium_amount'),
                row_dict.get('decision'),
                row_dict.get('created_at')
            ))
        
        if data:
            execute_batch(postgres_cursor, insert_query, data)
            self.postgres_conn.commit()
            logger.info(f"Migrated {len(data)} quotes")
        else:
            logger.info("No quotes to migrate")
    
    def migrate_all(self):
        """Migrate all tables."""
        self.connect()
        
        try:
            self.migrate_runs()
            self.migrate_human_reviews()
            self.migrate_quotes()
            
            logger.info("Migration completed successfully")
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            self.postgres_conn.rollback()
            raise
        finally:
            self.close()


def main():
    """Main migration function."""
    # Configuration
    sqlite_path = "storage/underwriting.db"
    
    postgres_config = {
        "host": os.getenv("POSTGRES_HOST", "localhost"),
        "port": int(os.getenv("POSTGRES_PORT", 5432)),
        "database": os.getenv("POSTGRES_DB", "agentic_underwriting"),
        "user": os.getenv("POSTGRES_USER", "postgres"),
        "password": os.getenv("POSTGRES_PASSWORD", "postgres")
    }
    
    # Check if SQLite database exists
    if not os.path.exists(sqlite_path):
        logger.warning(f"SQLite database not found at {sqlite_path}")
        logger.info("Skipping migration - no data to migrate")
        return
    
    # Run migration
    migrator = SQLiteToPostgresMigrator(sqlite_path, postgres_config)
    migrator.migrate_all()


if __name__ == "__main__":
    main()
