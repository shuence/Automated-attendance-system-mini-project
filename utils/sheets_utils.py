"""
Google Sheets utility functions for exporting attendance data.
Provides parallel export functionality alongside Excel exports.
"""
import logging
import os
import json
from typing import Optional, Dict, List, Any
import pandas as pd
from pathlib import Path

logger = logging.getLogger(__name__)

# Try to import Google Sheets libraries
try:
    import gspread
    from google.oauth2.service_account import Credentials
    from google.auth.exceptions import GoogleAuthError
    SHEETS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Google Sheets libraries not available: {str(e)}")
    SHEETS_AVAILABLE = False
    gspread = None
    Credentials = None
    GoogleAuthError = Exception

from config import (
    GOOGLE_SHEETS_ENABLED,
    GOOGLE_SHEETS_CREDENTIALS_FILE,
    GOOGLE_SHEETS_SPREADSHEET_ID,
    GOOGLE_SHEETS_SHARE_EMAIL,
    DEPARTMENT,
    YEAR,
    DIVISION,
    BASE_DIR
)

# Path to store the created spreadsheet ID
SPREADSHEET_ID_FILE = BASE_DIR / "db" / "google_sheets_id.json"


class GoogleSheetsExporter:
    """Handles Google Sheets export operations."""
    
    def __init__(self):
        self.client = None
        self.spreadsheet = None
        self._initialized = False
        self.created_spreadsheet_id = None
        self.created_spreadsheet_url = None
        self.created_spreadsheet_title = None
        
        if not SHEETS_AVAILABLE:
            logger.warning("Google Sheets libraries not installed. Install with: pip install gspread google-auth google-auth-oauthlib google-auth-httplib2")
            return
            
        if not GOOGLE_SHEETS_ENABLED:
            logger.info("Google Sheets export is disabled in configuration")
            return
            
        self._initialize_client()
    
    def _initialize_client(self) -> bool:
        """Initialize Google Sheets client with credentials."""
        try:
            credentials_path = Path(GOOGLE_SHEETS_CREDENTIALS_FILE)
            
            if not credentials_path.exists():
                logger.warning(f"Google Sheets credentials file not found: {credentials_path}")
                logger.info("To enable Google Sheets export:")
                logger.info("1. Create a service account in Google Cloud Console")
                logger.info("2. Download the JSON credentials file")
                logger.info("3. Place it at the path specified in GOOGLE_SHEETS_CREDENTIALS_FILE")
                logger.info("4. Share your Google Sheet with the service account email")
                return False
            
            # Authenticate with service account
            scope = [
                'https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive'
            ]
            
            creds = Credentials.from_service_account_file(
                str(credentials_path),
                scopes=scope
            )
            
            self.client = gspread.authorize(creds)
            self._initialized = True
            logger.info("Google Sheets client initialized successfully")
            return True
            
        except GoogleAuthError as e:
            logger.error(f"Google Sheets authentication error: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error initializing Google Sheets client: {str(e)}")
            return False
    
    def _load_saved_spreadsheet_id(self) -> Optional[str]:
        """Load saved spreadsheet ID from file."""
        try:
            if SPREADSHEET_ID_FILE.exists():
                with open(SPREADSHEET_ID_FILE, 'r') as f:
                    data = json.load(f)
                    return data.get('spreadsheet_id')
        except Exception as e:
            logger.warning(f"Could not load saved spreadsheet ID: {str(e)}")
        return None
    
    def _save_spreadsheet_id(self, spreadsheet_id: str, spreadsheet_url: str, title: str):
        """Save spreadsheet ID to file for future use."""
        try:
            # Ensure directory exists
            SPREADSHEET_ID_FILE.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                'spreadsheet_id': spreadsheet_id,
                'spreadsheet_url': spreadsheet_url,
                'title': title,
                'created_at': pd.Timestamp.now().isoformat()
            }
            
            with open(SPREADSHEET_ID_FILE, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Saved spreadsheet ID to {SPREADSHEET_ID_FILE}")
        except Exception as e:
            logger.warning(f"Could not save spreadsheet ID: {str(e)}")
    
    def _get_or_create_spreadsheet(self, spreadsheet_id: Optional[str] = None) -> Optional[Any]:
        """Get existing spreadsheet or create a new one."""
        try:
            # If no spreadsheet_id provided, try to load from saved file
            if not spreadsheet_id:
                spreadsheet_id = self._load_saved_spreadsheet_id()
                if spreadsheet_id:
                    logger.info(f"Using saved spreadsheet ID: {spreadsheet_id}")
            
            # If we have a spreadsheet_id, try to open it
            if spreadsheet_id:
                try:
                    spreadsheet = self.client.open_by_key(spreadsheet_id)
                    logger.info(f"Opened existing spreadsheet: {spreadsheet.title}")
                    return spreadsheet
                except Exception as e:
                    logger.warning(f"Could not open spreadsheet with ID {spreadsheet_id}: {str(e)}")
                    logger.info("Will create a new spreadsheet instead")
            
            # Create a new spreadsheet
            title = f"Attendance_{DEPARTMENT}_{YEAR}{DIVISION}"
            spreadsheet = self.client.create(title)
            
            # Share the spreadsheet with the configured email
            if GOOGLE_SHEETS_SHARE_EMAIL:
                self._share_spreadsheet(spreadsheet, GOOGLE_SHEETS_SHARE_EMAIL, role='writer')
            
            # Save the spreadsheet ID for future use
            self._save_spreadsheet_id(spreadsheet.id, spreadsheet.url, spreadsheet.title)
            
            logger.info(f"✅ Created new spreadsheet: {spreadsheet.title}")
            logger.info(f"📊 Spreadsheet ID: {spreadsheet.id}")
            logger.info(f"🔗 Spreadsheet URL: {spreadsheet.url}")
            if GOOGLE_SHEETS_SHARE_EMAIL:
                logger.info(f"👤 Shared with: {GOOGLE_SHEETS_SHARE_EMAIL}")
            
            # Store in instance for easy access
            self.created_spreadsheet_id = spreadsheet.id
            self.created_spreadsheet_url = spreadsheet.url
            self.created_spreadsheet_title = spreadsheet.title
            
            return spreadsheet
            
        except Exception as e:
            logger.error(f"Error getting/creating spreadsheet: {str(e)}")
            return None
    
    def _share_spreadsheet(self, spreadsheet: Any, email: str, role: str = "writer") -> bool:
        """
        Share the spreadsheet with the specified email address.
        
        Args:
            spreadsheet: The spreadsheet object to share
            email: Email address to share with
            role: Permission role ('reader', 'writer', or 'owner')
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not email:
                return False
            
            spreadsheet.share(email, perm_type='user', role=role)
            logger.info(f"✅ Shared spreadsheet with {email} (role: {role})")
            return True
        except Exception as e:
            logger.error(f"Error sharing spreadsheet with {email}: {str(e)}")
            return False
    
    def _get_or_create_worksheet(self, spreadsheet: Any, worksheet_name: str) -> Optional[Any]:
        """Get existing worksheet or create a new one."""
        try:
            # Try to get existing worksheet
            try:
                worksheet = spreadsheet.worksheet(worksheet_name)
                logger.info(f"Using existing worksheet: {worksheet_name}")
                return worksheet
            except gspread.exceptions.WorksheetNotFound:
                # Create new worksheet
                worksheet = spreadsheet.add_worksheet(
                    title=worksheet_name,
                    rows=1000,
                    cols=50
                )
                logger.info(f"Created new worksheet: {worksheet_name}")
                return worksheet
                
        except Exception as e:
            logger.error(f"Error getting/creating worksheet {worksheet_name}: {str(e)}")
            return None
    
    def _dataframe_to_sheets_format(self, df: pd.DataFrame) -> List[List[Any]]:
        """Convert pandas DataFrame to Google Sheets format (list of lists)."""
        # Convert DataFrame to list of lists
        # First row is headers
        data = [df.columns.tolist()]
        
        # Add data rows
        for _, row in df.iterrows():
            # Convert values to strings, handling NaN
            row_data = []
            for val in row:
                if pd.isna(val):
                    row_data.append("")
                elif isinstance(val, (int, float)):
                    row_data.append(val)
                else:
                    row_data.append(str(val))
            data.append(row_data)
        
        return data
    
    def export_dataframe(
        self,
        df: pd.DataFrame,
        worksheet_name: str,
        spreadsheet_id: Optional[str] = None,
        clear_existing: bool = False
    ) -> bool:
        """
        Export a pandas DataFrame to Google Sheets.
        
        Args:
            df: DataFrame to export
            worksheet_name: Name of the worksheet
            spreadsheet_id: Optional spreadsheet ID (uses config default if not provided)
            clear_existing: Whether to clear existing data before writing
            
        Returns:
            True if successful, False otherwise
        """
        if not self._initialized or not self.client:
            logger.warning("Google Sheets client not initialized. Skipping export.")
            return False
        
        try:
            # Get or create spreadsheet
            spreadsheet_id = spreadsheet_id or GOOGLE_SHEETS_SPREADSHEET_ID
            spreadsheet = self._get_or_create_spreadsheet(spreadsheet_id)
            
            if not spreadsheet:
                return False
            
            # Store spreadsheet reference
            self.spreadsheet = spreadsheet
            
            # Get or create worksheet
            worksheet = self._get_or_create_worksheet(spreadsheet, worksheet_name)
            
            if not worksheet:
                return False
            
            # Convert DataFrame to sheets format
            data = self._dataframe_to_sheets_format(df)
            
            # Clear existing data if requested
            if clear_existing:
                worksheet.clear()
            
            # Write data to worksheet
            # Use batch update for better performance
            worksheet.update('A1', data, value_input_option='USER_ENTERED')
            
            # Format header row (make it bold)
            if len(data) > 0:
                worksheet.format('A1:Z1', {
                    'textFormat': {'bold': True},
                    'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9}
                })
            
            logger.info(f"Successfully exported {len(df)} rows to worksheet '{worksheet_name}'")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting to Google Sheets: {str(e)}")
            return False
    
    def update_attendance_sheet(
        self,
        df: pd.DataFrame,
        subject_name: str,
        spreadsheet_id: Optional[str] = None
    ) -> bool:
        """
        Update attendance sheet for a specific subject.
        Merges new data with existing data (similar to Excel merge logic).
        
        Args:
            df: DataFrame with attendance data
            subject_name: Name of the subject
            spreadsheet_id: Optional spreadsheet ID
            
        Returns:
            True if successful, False otherwise
        """
        if not self._initialized or not self.client:
            return False
        
        try:
            spreadsheet_id = spreadsheet_id or GOOGLE_SHEETS_SPREADSHEET_ID
            spreadsheet = self._get_or_create_spreadsheet(spreadsheet_id)
            
            if not spreadsheet:
                return False
            
            worksheet_name = f"{subject_name}_{DEPARTMENT}_{YEAR}{DIVISION}"
            worksheet = self._get_or_create_worksheet(spreadsheet, worksheet_name)
            
            if not worksheet:
                return False
            
            # Get existing data if any
            try:
                existing_data = worksheet.get_all_values()
                if existing_data and len(existing_data) > 1:
                    # Convert to DataFrame
                    existing_df = pd.DataFrame(existing_data[1:], columns=existing_data[0])
                    
                    # Merge with new data
                    # Use outer join to keep all students and dates
                    merged_df = pd.merge(
                        existing_df,
                        df,
                        on=["Roll No", "Name"],
                        how="outer",
                        suffixes=('', '_new')
                    )
                    
                    # Handle date columns - prefer new data if both exist
                    for col in df.columns:
                        if col not in ["Roll No", "Name"]:
                            if f"{col}_new" in merged_df.columns:
                                # Use new value if available, otherwise keep old
                                merged_df[col] = merged_df[f"{col}_new"].fillna(merged_df[col])
                                merged_df = merged_df.drop(columns=[f"{col}_new"])
                    
                    # Recalculate summary statistics if they exist
                    if "Present" in merged_df.columns and "Total" in merged_df.columns:
                        date_cols = [col for col in merged_df.columns 
                                    if col not in ["Roll No", "Name", "Present", "Total", "Attendance %"]]
                        for i, row in merged_df.iterrows():
                            present_count = sum(1 for col in date_cols 
                                              if row.get(col) == "✅" or str(row.get(col, "")).strip() == "✅")
                            total_count = sum(1 for col in date_cols 
                                            if row.get(col) in ["✅", "❌"] or 
                                            str(row.get(col, "")).strip() in ["✅", "❌"])
                            merged_df.at[i, "Present"] = present_count
                            merged_df.at[i, "Total"] = total_count
                            if total_count > 0:
                                merged_df.at[i, "Attendance %"] = round(present_count / total_count * 100, 1)
                            else:
                                merged_df.at[i, "Attendance %"] = 0.0
                    
                    df = merged_df
                    
            except Exception as e:
                logger.info(f"No existing data found or error reading: {str(e)}. Creating new sheet.")
            
            # Export the merged/new data
            return self.export_dataframe(df, worksheet_name, spreadsheet_id, clear_existing=True)
            
        except Exception as e:
            logger.error(f"Error updating attendance sheet: {str(e)}")
            return False
    
    def get_spreadsheet_info(self) -> Optional[Dict[str, str]]:
        """Get information about the current spreadsheet."""
        if not self.spreadsheet:
            return None
        
        try:
            return {
                'id': self.spreadsheet.id,
                'url': self.spreadsheet.url,
                'title': self.spreadsheet.title
            }
        except:
            # Fallback to saved info
            if self.created_spreadsheet_id:
                return {
                    'id': self.created_spreadsheet_id,
                    'url': self.created_spreadsheet_url or '',
                    'title': self.created_spreadsheet_title or ''
                }
            return None


# Global exporter instance
_exporter_instance: Optional[GoogleSheetsExporter] = None


def get_sheets_exporter() -> Optional[GoogleSheetsExporter]:
    """Get or create the global Google Sheets exporter instance."""
    global _exporter_instance
    
    if not GOOGLE_SHEETS_ENABLED:
        return None
    
    if _exporter_instance is None:
        _exporter_instance = GoogleSheetsExporter()
    
    return _exporter_instance if _exporter_instance._initialized else None


def export_to_sheets(
    df: pd.DataFrame,
    worksheet_name: str,
    spreadsheet_id: Optional[str] = None,
    clear_existing: bool = False
) -> bool:
    """
    Convenience function to export DataFrame to Google Sheets.
    
    Args:
        df: DataFrame to export
        worksheet_name: Name of the worksheet
        spreadsheet_id: Optional spreadsheet ID
        clear_existing: Whether to clear existing data
        
    Returns:
        True if successful, False otherwise
    """
    exporter = get_sheets_exporter()
    if not exporter:
        return False
    
    return exporter.export_dataframe(df, worksheet_name, spreadsheet_id, clear_existing)


def update_attendance_sheet(
    df: pd.DataFrame,
    subject_name: str,
    spreadsheet_id: Optional[str] = None
) -> bool:
    """
    Convenience function to update attendance sheet for a subject.
    
    Args:
        df: DataFrame with attendance data
        subject_name: Name of the subject
        spreadsheet_id: Optional spreadsheet ID
        
    Returns:
        True if successful, False otherwise
    """
    exporter = get_sheets_exporter()
    if not exporter:
        return False
    
    return exporter.update_attendance_sheet(df, subject_name, spreadsheet_id)


def get_spreadsheet_info() -> Optional[Dict[str, str]]:
    """
    Get information about the current Google Sheets spreadsheet.
    
    Returns:
        Dictionary with 'id', 'url', and 'title' keys, or None if not available
    """
    exporter = get_sheets_exporter()
    if not exporter:
        return None
    
    return exporter.get_spreadsheet_info()

