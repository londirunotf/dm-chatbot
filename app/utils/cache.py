"""
キャッシュユーティリティ
- FAQ キャッシュ
- 統計データキャッシュ
- 静的リソースキャッシュ
"""

import time
import hashlib
import json
from functools import wraps
from datetime import datetime, timedelta
from flask import current_app

class SimpleCache:
    """シンプルなメモリキャッシュ"""
    
    def __init__(self):
        self._cache = {}
        self._timestamps = {}
    
    def get(self, key):
        """キャッシュから値を取得"""
        if key in self._cache:
            timestamp = self._timestamps.get(key, 0)
            if timestamp > time.time():  # まだ有効
                return self._cache[key]
            else:  # 期限切れ
                self.delete(key)
        return None
    
    def set(self, key, value, timeout=300):
        """キャッシュに値を設定（デフォルト5分）"""
        self._cache[key] = value
        self._timestamps[key] = time.time() + timeout
    
    def delete(self, key):
        """キャッシュから削除"""
        self._cache.pop(key, None)
        self._timestamps.pop(key, None)
    
    def clear(self):
        """全キャッシュクリア"""
        self._cache.clear()
        self._timestamps.clear()
    
    def stats(self):
        """キャッシュ統計"""
        current_time = time.time()
        valid_keys = [k for k, t in self._timestamps.items() if t > current_time]
        return {
            'total_keys': len(self._cache),
            'valid_keys': len(valid_keys),
            'expired_keys': len(self._cache) - len(valid_keys)
        }

# グローバルキャッシュインスタンス
_cache = SimpleCache()

def get_cache_key(*args, **kwargs):
    """キャッシュキー生成"""
    key_data = {
        'args': args,
        'kwargs': kwargs
    }
    key_string = json.dumps(key_data, sort_keys=True)
    return hashlib.md5(key_string.encode()).hexdigest()

def cached(timeout=300, key_prefix=''):
    """キャッシュデコレータ"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # キャッシュキー生成
            cache_key = f"{key_prefix}:{func.__name__}:{get_cache_key(*args, **kwargs)}"
            
            # キャッシュから取得試行
            result = _cache.get(cache_key)
            if result is not None:
                return result
            
            # キャッシュにない場合は実行
            result = func(*args, **kwargs)
            
            # 結果をキャッシュに保存
            _cache.set(cache_key, result, timeout)
            
            return result
        return wrapper
    return decorator

def cache_faq_data(timeout=600):
    """FAQ専用キャッシュ（10分）"""
    return cached(timeout=timeout, key_prefix='faq')

def cache_stats_data(timeout=300):
    """統計データ専用キャッシュ（5分）"""
    return cached(timeout=timeout, key_prefix='stats')

def cache_user_data(timeout=180):
    """ユーザーデータ専用キャッシュ（3分）"""
    return cached(timeout=timeout, key_prefix='user')

def invalidate_cache(pattern=None):
    """キャッシュ無効化"""
    if pattern:
        # パターンマッチングでキャッシュクリア
        keys_to_delete = []
        for key in _cache._cache.keys():
            if pattern in key:
                keys_to_delete.append(key)
        
        for key in keys_to_delete:
            _cache.delete(key)
    else:
        # 全キャッシュクリア
        _cache.clear()

def get_cache_stats():
    """キャッシュ統計取得"""
    return _cache.stats()

# Flask レスポンスキャッシュヘルパー
def add_cache_headers(response, max_age=300):
    """レスポンスにキャッシュヘッダーを追加"""
    response.cache_control.max_age = max_age
    response.cache_control.public = True
    
    # ETageも追加
    if response.data:
        etag = hashlib.md5(response.data).hexdigest()
        response.set_etag(etag)
    
    return response

def add_no_cache_headers(response):
    """キャッシュ無効ヘッダーを追加"""
    response.cache_control.no_cache = True
    response.cache_control.no_store = True
    response.cache_control.must_revalidate = True
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response