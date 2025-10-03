import os
import duckdb
from datetime import datetime
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv
load_dotenv()


class JiraDBManager:
    def __init__(self):
        self.db_dir = os.path.expanduser(os.getenv("DB_LOCATION", "./"))
        self.db_path = os.path.join(self.db_dir, "jira_history.duckdb")
        self._ensure_db_exists()
        
    def _ensure_db_exists(self):
        """Ensure database directory and tables exist"""
        if not os.path.exists(self.db_dir):
            os.makedirs(self.db_dir)
            
        # Connect and create tables if they don't exist
        with duckdb.connect(self.db_path) as con:
            # Issues table
            con.execute("""
                CREATE TABLE IF NOT EXISTS issues (
                    key VARCHAR PRIMARY KEY,
                    type VARCHAR,
                    title VARCHAR,
                    parent_key VARCHAR,
                    status VARCHAR,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Comments table
            con.execute("""
                CREATE TABLE IF NOT EXISTS comments (
                    id VARCHAR PRIMARY KEY,
                    issue_key VARCHAR,
                    author VARCHAR,
                    content TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (issue_key) REFERENCES issues(key)
                );
            """)
            
            # Transitions table
            con.execute("""
                CREATE TABLE IF NOT EXISTS transitions (
                    id BIGINT PRIMARY KEY,
                    issue_key VARCHAR,
                    from_status VARCHAR,
                    to_status VARCHAR,
                    transitioned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (issue_key) REFERENCES issues(key)
                );
            """)
    
    def store_issue(self, issue_key: str, issue_type: str, title: str, 
                    parent_key: Optional[str] = None, status: Optional[str] = None) -> None:
        """Store information about a created issue"""
        with duckdb.connect(self.db_path) as con:
            con.execute("""
                INSERT INTO issues (key, type, title, parent_key, status)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT (key) DO UPDATE SET
                    title = excluded.title,
                    status = excluded.status,
                    last_updated = CURRENT_TIMESTAMP;
            """, [issue_key, issue_type, title, parent_key, status])
    
    def update_issue_status(self, issue_key: str, new_status: str, 
                          old_status: Optional[str] = None) -> None:
        """Update the status of a tracked issue"""
        with duckdb.connect(self.db_path) as con:
            # Update issues table
            con.execute("""
                UPDATE issues 
                SET status = ?, last_updated = CURRENT_TIMESTAMP
                WHERE key = ?;
            """, [new_status, issue_key])
            
            # Record transition
            con.execute("""
                INSERT INTO transitions (issue_key, from_status, to_status)
                VALUES (?, ?, ?);
            """, [issue_key, old_status, new_status])
    
    def get_issue_history(self, days: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get history of created issues, optionally filtered by number of days"""
        with duckdb.connect(self.db_path) as con:
            query = """
                SELECT 
                    i.key,
                    i.type,
                    i.title,
                    i.parent_key,
                    i.status,
                    i.created_at,
                    i.last_updated,
                    p.title as parent_title,
                    COUNT(c.id) as comments_count
                FROM issues i
                LEFT JOIN issues p ON i.parent_key = p.key
                LEFT JOIN comments c ON i.key = c.issue_key
            """
            
            if days:
                query += f" WHERE i.created_at >= CURRENT_TIMESTAMP - INTERVAL '{days} days'"
                
            query += " GROUP BY i.key, i.type, i.title, i.parent_key, i.status, i.created_at, i.last_updated, p.title"
            query += " ORDER BY i.created_at DESC"
            
            result = con.execute(query).fetchall()
            columns = ['key', 'type', 'title', 'parent_key', 'status', 'created_at', 
                      'last_updated', 'parent_title', 'comments_count']
            
            return [dict(zip(columns, row)) for row in result]
    
    def store_comment(self, comment_id: str, issue_key: str, 
                     author: str, content: str) -> None:
        """Store a comment"""
        with duckdb.connect(self.db_path) as con:
            con.execute("""
                INSERT INTO comments (id, issue_key, author, content)
                VALUES (?, ?, ?, ?);
            """, [comment_id, issue_key, author, content])
    
    def get_issue_statistics(self) -> Dict[str, Any]:
        """Get statistics about tracked issues"""
        with duckdb.connect(self.db_path) as con:
            stats = {}
            
            # Total issues by type
            result = con.execute("""
                SELECT type, COUNT(*) as count
                FROM issues
                GROUP BY type;
            """).fetchall()
            stats['issues_by_type'] = dict(result)
            
            # Active issues by status
            result = con.execute("""
                SELECT status, COUNT(*) as count
                FROM issues
                WHERE status IS NOT NULL
                GROUP BY status;
            """).fetchall()
            stats['issues_by_status'] = dict(result)
            
            # Comments statistics
            result = con.execute("""
                SELECT 
                    COUNT(*) as total_comments,
                    COUNT(DISTINCT issue_key) as issues_with_comments,
                    COUNT(DISTINCT author) as unique_commenters
                FROM comments;
            """).fetchone()
            stats['comments'] = {
                'total': result[0],
                'issues_with_comments': result[1],
                'unique_commenters': result[2]
            }
            
            return stats
        
    def update_issue(self, issue_key: str, **kwargs) -> None:
        """Update issue details in the database.
        
        Args:
            issue_key: The issue key to update
            **kwargs: Fields to update (title, status, parent_key, etc.)
        """
        with duckdb.connect(self.db_path) as con:
            # Build UPDATE query dynamically based on provided fields
            fields = []
            values = []
            for field, value in kwargs.items():
                fields.append(f"{field} = ?")
                values.append(value)
            
            if fields:
                fields.append("last_updated = CURRENT_TIMESTAMP")
                query = f"""
                    UPDATE issues 
                    SET {', '.join(fields)}
                    WHERE key = ?
                """
                values.append(issue_key)
                con.execute(query, values)