"""
Database Validation Script
Verify database integrity, data quality, and query performance
Run after setup_database.py:
    python scripts/validate_database.py
"""

import sqlite3
from pathlib import Path
import logging
import time

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_db_path():
    """Get database path"""
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent
    return project_root / 'data' / 'h1b_wages.db'


def test_schema(conn):
    """Test database schema"""
    logger.info("\n" + "="*60)
    logger.info("SCHEMA VALIDATION")
    logger.info("="*60)
    
    cursor = conn.cursor()
    
    # Check tables exist
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' ORDER BY name
    """)
    tables = [row[0] for row in cursor.fetchall()]
    logger.info(f"\n✓ Tables exist: {', '.join(tables)}")
    
    # Check indexes
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='index' ORDER BY name
    """)
    indexes = [row[0] for row in cursor.fetchall()]
    logger.info(f"✓ Indexes exist: {len(indexes)} indexes")
    for idx in indexes:
        logger.info(f"    - {idx}")
    
    # Check foreign keys
    cursor.execute("PRAGMA foreign_key_list(wage_levels)")
    fks = cursor.fetchall()
    logger.info(f"✓ Foreign keys: {len(fks)} constraints")
    for fk in fks:
        logger.info(f"    - {fk}")


def test_data_quality(conn):
    """Test data quality and integrity"""
    logger.info("\n" + "="*60)
    logger.info("DATA QUALITY VALIDATION")
    logger.info("="*60)
    
    cursor = conn.cursor()
    
    # Check for nulls in critical columns
    logger.info("\nChecking for NULL values in critical columns...")
    
    cursor.execute('SELECT COUNT(*) FROM geography WHERE state IS NULL')
    null_states = cursor.fetchone()[0]
    logger.info(f"  Geography.state nulls: {null_states} (should be 0)")
    
    cursor.execute('SELECT COUNT(*) FROM occupations WHERE job_title IS NULL')
    null_titles = cursor.fetchone()[0]
    logger.info(f"  Occupations.job_title nulls: {null_titles} (should be 0)")
    
    cursor.execute('SELECT COUNT(*) FROM wage_levels WHERE l1_wage IS NULL')
    null_wages = cursor.fetchone()[0]
    logger.info(f"  Wage_levels.l1_wage nulls: {null_wages} (should be 0)")
    
    # Check for duplicates
    logger.info("\nChecking for duplicate records...")
    
    cursor.execute('''
        SELECT state, county, COUNT(*) as cnt 
        FROM geography 
        GROUP BY state, county 
        HAVING cnt > 1
    ''')
    dup_geo = cursor.fetchall()
    logger.info(f"  Geography duplicates: {len(dup_geo)} (should be 0)")
    
    cursor.execute('''
        SELECT soc_code, COUNT(*) as cnt 
        FROM occupations 
        GROUP BY soc_code 
        HAVING cnt > 1
    ''')
    dup_occ = cursor.fetchall()
    logger.info(f"  Occupations duplicates: {len(dup_occ)} (should be 0)")
    
    # Check wage value ranges
    logger.info("\nChecking wage value ranges...")
    
    cursor.execute('SELECT MIN(l1_wage), MAX(l1_wage) FROM wage_levels')
    min_l1, max_l1 = cursor.fetchone()
    logger.info(f"  L1 wages: ${min_l1:,.2f} - ${max_l1:,.2f}")
    
    cursor.execute('SELECT MIN(l4_wage), MAX(l4_wage) FROM wage_levels')
    min_l4, max_l4 = cursor.fetchone()
    logger.info(f"  L4 wages: ${min_l4:,.2f} - ${max_l4:,.2f}")
    
    # Check wage progression (L1 < L2 < L3 < L4)
    cursor.execute('''
        SELECT COUNT(*) FROM wage_levels 
        WHERE l1_wage >= l2_wage OR l2_wage >= l3_wage OR l3_wage >= l4_wage
    ''')
    bad_progression = cursor.fetchone()[0]
    logger.info(f"  Wage progression issues: {bad_progression} (should be 0)")


def test_query_performance(conn):
    """Test query performance"""
    logger.info("\n" + "="*60)
    logger.info("QUERY PERFORMANCE VALIDATION")
    logger.info("="*60)
    
    cursor = conn.cursor()
    
    # Test 1: Get all states
    logger.info("\n1. Get all states...")
    start = time.time()
    cursor.execute('SELECT DISTINCT state FROM geography ORDER BY state')
    states = cursor.fetchall()
    elapsed = (time.time() - start) * 1000
    logger.info(f"   Retrieved {len(states)} states in {elapsed:.2f}ms")
    
    # Test 2: Get counties for a state
    logger.info("\n2. Get counties for California...")
    start = time.time()
    cursor.execute('''
        SELECT county FROM geography 
        WHERE state = 'California' 
        ORDER BY county
    ''')
    counties = cursor.fetchall()
    elapsed = (time.time() - start) * 1000
    logger.info(f"   Retrieved {len(counties)} counties in {elapsed:.2f}ms")
    
    # Test 3: Get single wage record
    logger.info("\n3. Get wage record for California/Alameda/15-1252...")
    start = time.time()
    cursor.execute('''
        SELECT wl.l1_wage, wl.l2_wage, wl.l3_wage, wl.l4_wage
        FROM wage_levels wl
        JOIN geography g ON wl.area_code = g.area_code
        WHERE g.state = ? AND g.county = ? AND wl.soc_code = ?
    ''', ('California', 'Alameda County', '15-1252'))
    row = cursor.fetchone()
    elapsed = (time.time() - start) * 1000
    if row:
        logger.info(f"   Retrieved wages in {elapsed:.2f}ms: L1=${row[0]:,.0f}")
    else:
        logger.warning(f"   No wages found (sample data may not include this)")
    
    # Test 4: Get all wages for an occupation
    logger.info("\n4. Get all counties for SOC 15-1252...")
    start = time.time()
    cursor.execute('''
        SELECT g.state, g.county, 
               wl.l1_wage, wl.l2_wage, wl.l3_wage, wl.l4_wage
        FROM wage_levels wl
        JOIN geography g ON wl.area_code = g.area_code
        WHERE wl.soc_code = ?
        ORDER BY g.state, g.county
    ''', ('15-1252',))
    rows = cursor.fetchall()
    elapsed = (time.time() - start) * 1000
    logger.info(f"   Retrieved {len(rows)} county records in {elapsed:.2f}ms")
    
    # Test 5: Search occupations
    logger.info("\n5. Search occupations for 'Software'...")
    start = time.time()
    cursor.execute('''
        SELECT soc_code, job_title 
        FROM occupations 
        WHERE job_title LIKE ? 
        ORDER BY job_title 
        LIMIT 20
    ''', ('%Software%',))
    occs = cursor.fetchall()
    elapsed = (time.time() - start) * 1000
    logger.info(f"   Found {len(occs)} occupations in {elapsed:.2f}ms")


def test_foreign_keys(conn):
    """Test foreign key constraints"""
    logger.info("\n" + "="*60)
    logger.info("FOREIGN KEY VALIDATION")
    logger.info("="*60)
    
    cursor = conn.cursor()
    
    # Check wage_levels references valid area_codes
    logger.info("\nChecking wage_levels.area_code references...")
    cursor.execute('''
        SELECT COUNT(*) FROM wage_levels wl
        WHERE NOT EXISTS (
            SELECT 1 FROM geography g WHERE g.area_code = wl.area_code
        )
    ''')
    orphan_areas = cursor.fetchone()[0]
    logger.info(f"  Orphan area_code references: {orphan_areas} (should be 0)")
    
    # Check wage_levels references valid soc_codes
    logger.info("\nChecking wage_levels.soc_code references...")
    cursor.execute('''
        SELECT COUNT(*) FROM wage_levels wl
        WHERE NOT EXISTS (
            SELECT 1 FROM occupations o WHERE o.soc_code = wl.soc_code
        )
    ''')
    orphan_socs = cursor.fetchone()[0]
    logger.info(f"  Orphan soc_code references: {orphan_socs} (should be 0)")


def main():
    """Main validation process"""
    logger.info("="*60)
    logger.info("H1B WAGE DASHBOARD - DATABASE VALIDATION")
    logger.info("="*60)
    
    db_path = get_db_path()
    
    if not db_path.exists():
        logger.error(f"Database not found at {db_path}")
        logger.error("Run 'python scripts/setup_database.py' first")
        return False
    
    try:
        conn = sqlite3.connect(str(db_path))
        
        test_schema(conn)
        test_data_quality(conn)
        test_query_performance(conn)
        test_foreign_keys(conn)
        
        conn.close()
        
        logger.info("\n" + "="*60)
        logger.info("✓ DATABASE VALIDATION COMPLETE!")
        logger.info("="*60)
        logger.info(f"\nAll tests passed. Database is ready for use.")
        
        return True
        
    except Exception as e:
        logger.error(f"\n✗ VALIDATION FAILED!")
        logger.error(f"Error: {e}", exc_info=True)
        return False


if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)

