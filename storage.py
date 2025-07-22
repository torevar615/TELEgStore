import json
import os
import uuid
from datetime import datetime
from typing import List, Dict, Optional, Any
from models import Category, File, Subscriber, BroadcastMessage

class Storage:
    def __init__(self):
        self.data_dir = "data"
        self.categories_file = os.path.join(self.data_dir, "categories.json")
        self.files_file = os.path.join(self.data_dir, "files.json")
        self.subscribers_file = os.path.join(self.data_dir, "subscribers.json")
        self.settings_file = os.path.join(self.data_dir, "settings.json")
        self.pending_files_file = os.path.join(self.data_dir, "pending_files.json")
        
        # Ensure data directory exists
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Initialize files if they don't exist
        self._init_files()
    
    def _init_files(self):
        """Initialize JSON files with empty data if they don't exist"""
        files_to_init = [
            (self.categories_file, []),
            (self.files_file, []),
            (self.subscribers_file, []),
            (self.settings_file, {"admin_id": None, "storage_channel_id": None}),
            (self.pending_files_file, [])
        ]
        
        for file_path, default_data in files_to_init:
            if not os.path.exists(file_path):
                self._save_json(file_path, default_data)
    
    def _load_json(self, file_path: str) -> Any:
        """Load data from JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return [] if file_path != self.settings_file else {}
    
    def _save_json(self, file_path: str, data: Any):
        """Save data to JSON file"""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    # Category methods
    def get_categories(self) -> List[Dict[str, Any]]:
        """Get all categories"""
        return self._load_json(self.categories_file)
    
    def get_category(self, category_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific category by ID"""
        categories = self.get_categories()
        return next((cat for cat in categories if cat['id'] == category_id), None)
    
    def get_subcategories(self, parent_id: str) -> List[Dict[str, Any]]:
        """Get subcategories of a parent category"""
        categories = self.get_categories()
        return [cat for cat in categories if cat.get('parent_id') == parent_id]
    
    def add_category(self, name: str, description: str = None, parent_id: str = None) -> str:
        """Add a new category"""
        categories = self.get_categories()
        
        category_id = str(uuid.uuid4())
        category = {
            'id': category_id,
            'name': name,
            'description': description,
            'parent_id': parent_id,
            'created_at': datetime.now().isoformat()
        }
        
        categories.append(category)
        self._save_json(self.categories_file, categories)
        return category_id
    
    def update_category(self, category_id: str, name: str = None, description: str = None) -> bool:
        """Update a category"""
        categories = self.get_categories()
        
        for category in categories:
            if category['id'] == category_id:
                if name is not None:
                    category['name'] = name
                if description is not None:
                    category['description'] = description
                self._save_json(self.categories_file, categories)
                return True
        return False
    
    def delete_category(self, category_id: str) -> bool:
        """Delete a category and its subcategories"""
        categories = self.get_categories()
        files = self.get_files()
        
        # Find all subcategory IDs to delete
        def get_all_subcategory_ids(parent_id):
            subcats = [cat['id'] for cat in categories if cat.get('parent_id') == parent_id]
            all_ids = subcats.copy()
            for subcat_id in subcats:
                all_ids.extend(get_all_subcategory_ids(subcat_id))
            return all_ids
        
        ids_to_delete = [category_id] + get_all_subcategory_ids(category_id)
        
        # Remove categories
        categories = [cat for cat in categories if cat['id'] not in ids_to_delete]
        self._save_json(self.categories_file, categories)
        
        # Remove files in these categories
        files = [f for f in files if f.get('category_id') not in ids_to_delete]
        self._save_json(self.files_file, files)
        
        return True
    
    # File methods
    def get_files(self) -> List[Dict[str, Any]]:
        """Get all files"""
        return self._load_json(self.files_file)
    
    def get_file(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific file by ID"""
        files = self.get_files()
        return next((f for f in files if f['id'] == file_id), None)
    
    def get_files_by_category(self, category_id: str) -> List[Dict[str, Any]]:
        """Get files in a specific category"""
        files = self.get_files()
        return [f for f in files if f.get('category_id') == category_id]
    
    def add_file(self, name: str, category_id: str, telegram_file_id: str = None, 
                description: str = None, size: int = None, mime_type: str = None) -> str:
        """Add a new file"""
        files = self.get_files()
        
        file_id = str(uuid.uuid4())
        file_data = {
            'id': file_id,
            'name': name,
            'category_id': category_id,
            'telegram_file_id': telegram_file_id,
            'description': description,
            'size': size,
            'mime_type': mime_type,
            'created_at': datetime.now().isoformat()
        }
        
        files.append(file_data)
        self._save_json(self.files_file, files)
        return file_id
    
    def update_file(self, file_id: str, **kwargs) -> bool:
        """Update a file"""
        files = self.get_files()
        
        for file_data in files:
            if file_data['id'] == file_id:
                for key, value in kwargs.items():
                    if key in ['name', 'category_id', 'telegram_file_id', 'description', 'size', 'mime_type']:
                        file_data[key] = value
                self._save_json(self.files_file, files)
                return True
        return False
    
    def delete_file(self, file_id: str) -> bool:
        """Delete a file"""
        files = self.get_files()
        original_count = len(files)
        files = [f for f in files if f['id'] != file_id]
        
        if len(files) < original_count:
            self._save_json(self.files_file, files)
            return True
        return False
    
    # Subscriber methods
    def get_subscribers(self) -> List[Dict[str, Any]]:
        """Get all subscribers"""
        return self._load_json(self.subscribers_file)
    
    def add_subscriber(self, user_id: int, first_name: str = None, username: str = None):
        """Add a new subscriber"""
        subscribers = self.get_subscribers()
        
        # Check if subscriber already exists
        existing = next((s for s in subscribers if s['user_id'] == user_id), None)
        if existing:
            existing['is_active'] = True
            existing['first_name'] = first_name or existing.get('first_name')
            existing['username'] = username or existing.get('username')
        else:
            subscriber = {
                'user_id': user_id,
                'first_name': first_name,
                'username': username,
                'joined_at': datetime.now().isoformat(),
                'is_active': True
            }
            subscribers.append(subscriber)
        
        self._save_json(self.subscribers_file, subscribers)
    
    def get_active_subscribers(self) -> List[Dict[str, Any]]:
        """Get all active subscribers"""
        subscribers = self.get_subscribers()
        return [s for s in subscribers if s.get('is_active', True)]
    
    # Pending files methods
    def save_pending_file(self, file_data: Dict[str, Any]):
        """Save a pending file upload"""
        pending_files = self._load_json(self.pending_files_file)
        file_data['id'] = str(uuid.uuid4())
        pending_files.append(file_data)
        self._save_json(self.pending_files_file, pending_files)
    
    def get_pending_files(self) -> List[Dict[str, Any]]:
        """Get all pending files"""
        return self._load_json(self.pending_files_file)
    
    def remove_pending_file(self, file_id: str):
        """Remove a pending file"""
        pending_files = self.get_pending_files()
        pending_files = [f for f in pending_files if f.get('id') != file_id]
        self._save_json(self.pending_files_file, pending_files)
    
    # Settings methods
    def get_settings(self) -> Dict[str, Any]:
        """Get bot settings"""
        return self._load_json(self.settings_file)
    
    def update_settings(self, **kwargs):
        """Update bot settings"""
        settings = self.get_settings()
        settings.update(kwargs)
        self._save_json(self.settings_file, settings)
