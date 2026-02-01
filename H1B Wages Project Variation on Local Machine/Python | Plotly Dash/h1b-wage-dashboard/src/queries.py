"""
SQL Query Functions for H1B Wage Dashboard
All database queries with caching via @lru_cache
"""

from db import db
from functools import lru_cache
from typing import List, Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class WageQueries:
    """
    All SQL queries for wage data
    Methods cache results for performance
    """
    
    @staticmethod
    @lru_cache(maxsize=1)
    def get_all_states() -> List[str]:
        """
        Get distinct states (cached - calls DB only once)
        
        Returns:
            list: Sorted list of state names
            Example: ['Alabama', 'Alaska', 'Arizona', ...]
        """
        rows = db.execute_query('''
            SELECT DISTINCT state 
            FROM geography 
            ORDER BY state ASC
        ''')
        states = [row[0] for row in rows]
        logger.debug(f"Fetched {len(states)} states")
        return tuple(states)  # Cache requires immutable return
    
    @staticmethod
    @lru_cache(maxsize=256)
    def get_counties_for_state(state: str) -> Tuple[str, ...]:
        """
        Get counties for a specific state (cached per state)
        
        Args:
            state (str): State name (e.g., 'California')
        
        Returns:
            tuple: Sorted list of county names
            Example: ('Alameda County', 'Alpine County', ...)
        """
        rows = db.execute_query('''
            SELECT DISTINCT county 
            FROM geography 
            WHERE state = ? 
            ORDER BY county ASC
        ''', (state,))
        counties = tuple(row[0] for row in rows)
        logger.debug(f"Fetched {len(counties)} counties for {state}")
        return counties
    
    @staticmethod
    @lru_cache(maxsize=1)
    def get_all_occupations() -> Tuple[Dict, ...]:
        """
        Get all occupations (cached - calls DB only once)
        
        Returns:
            tuple: List of dicts with soc_code and job_title
            Example: [
                {'soc_code': '15-1252', 'job_title': 'Software Developers'},
                {'soc_code': '15-1243', 'job_title': 'Computer Network Architects'},
                ...
            ]
        """
        rows = db.execute_query('''
            SELECT soc_code, job_title 
            FROM occupations 
            ORDER BY job_title ASC
        ''')
        occupations = tuple(
            {'soc_code': row[0], 'job_title': row[1]} 
            for row in rows
        )
        logger.debug(f"Fetched {len(occupations)} occupations")
        return occupations
    
    @staticmethod
    def get_occupation_by_code(soc_code: str) -> Optional[Dict]:
        """
        Get single occupation by SOC code (not cached - specific lookup)
        
        Args:
            soc_code (str): SOC code (e.g., '15-1252')
        
        Returns:
            dict: {'soc_code', 'job_title', 'description'} or None
        """
        row = db.execute_single('''
            SELECT soc_code, job_title, description 
            FROM occupations 
            WHERE soc_code = ?
        ''', (soc_code,))
        
        if row:
            return {
                'soc_code': row[0],
                'job_title': row[1],
                'description': row[2]
            }
        logger.warning(f"No occupation found for SOC code: {soc_code}")
        return None
    
    @staticmethod
    def get_wage_levels(state: str, county: str, soc_code: str) -> Optional[Dict]:
        """
        Get L1-L4 wages for a specific location + occupation
        Direct lookup - NOT cached (depends on 3 variables)
        
        Args:
            state (str): State name
            county (str): County name
            soc_code (str): SOC code
        
        Returns:
            dict: {'L1': 89000.0, 'L2': 107000.0, 'L3': 125000.0, 'L4': 143000.0}
            or None if not found
        """
        row = db.execute_single('''
            SELECT wl.l1_wage, wl.l2_wage, wl.l3_wage, wl.l4_wage
            FROM wage_levels wl
            JOIN geography g ON wl.area_code = g.area_code
            WHERE g.state = ? AND g.county = ? AND wl.soc_code = ?
            LIMIT 1
        ''', (state, county, soc_code))
        
        if row:
            wages = {
                'L1': float(row[0]),
                'L2': float(row[1]),
                'L3': float(row[2]),
                'L4': float(row[3])
            }
            logger.debug(f"Fetched wages for {state}, {county}, {soc_code}")
            return wages
        
        logger.warning(f"No wages found for {state}, {county}, {soc_code}")
        return None
    
    @staticmethod
    def get_all_wages_for_occupation(soc_code: str) -> Dict[Tuple[str, str], Dict]:
        """
        Get ALL county wages for a specific occupation (for map visualization)
        NOT cached - returns large dataset
        
        Args:
            soc_code (str): SOC code
        
        Returns:
            dict: {(state, county): {'L1': ..., 'L2': ..., 'L3': ..., 'L4': ...}, ...}
            Example:
            {
                ('California', 'Alameda County'): {'L1': 89000, 'L2': 107000, ...},
                ('California', 'Alpine County'): {'L1': 91000, 'L2': 109000, ...},
                ...
            }
        """
        rows = db.execute_query('''
            SELECT g.state, g.county, 
                   wl.l1_wage, wl.l2_wage, wl.l3_wage, wl.l4_wage
            FROM wage_levels wl
            JOIN geography g ON wl.area_code = g.area_code
            WHERE wl.soc_code = ?
            ORDER BY g.state, g.county 
        ''', (soc_code,))
        
        result = {}
        for row in rows:
            state, county = row[0], row[1]
            result[(state, county)] = {
                'L1': float(row[2]),
                'L2': float(row[3]),
                'L3': float(row[4]),
                'L4': float(row[5])
            }
        
        logger.debug(f"Fetched {len(result)} county wages for {soc_code}")
        return result
    
    @staticmethod
    def search_occupations(search_term: str) -> List[Dict]:
        """
        Search occupations by title or code (autocomplete)
        NOT cached - depends on search term
        
        Args:
            search_term (str): Search text (e.g., 'software' or '15-1252')
        
        Returns:
            list: Matching occupations (max 20 results)
            Example: [
                {'soc_code': '15-1252', 'job_title': 'Software Developers'},
                {'soc_code': '15-1256', 'job_title': 'Software Quality Assurance Analysts'},
                ...
            ]
        """
        search_param = f"%{search_term}%"
        rows = db.execute_query('''
            SELECT soc_code, job_title 
            FROM occupations 
            WHERE soc_code LIKE ? OR job_title LIKE ?
            ORDER BY job_title ASC
            LIMIT 20
        ''', (search_param, search_param))
        
        results = [
            {'soc_code': row[0], 'job_title': row[1]} 
            for row in rows
        ]
        logger.debug(f"Found {len(results)} occupations matching '{search_term}'")
        return results
    
    @staticmethod
    def get_database_stats() -> Dict:
        """
        Get database statistics (for debugging/monitoring)
        
        Returns:
            dict: Database metadata and record counts
        """
        info = db.get_database_info()
        return {
            'database_path': info['path'],
            'size_mb': round(info['size_mb'], 2),
            'geography_records': info['geography_records'],
            'occupations_records': info['occupations_records'],
            'wage_levels_records': info['wage_levels_records'],
            'total_records': info['geography_records'] + info['occupations_records'] + info['wage_levels_records']
        }


# Singleton instance
queries = WageQueries()

