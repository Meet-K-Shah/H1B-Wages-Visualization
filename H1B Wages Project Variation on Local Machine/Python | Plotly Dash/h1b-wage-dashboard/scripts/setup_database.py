"""
Setup Script: Convert CSVs to SQLite Database
Run this ONCE at project initialization:
    python scripts/setup_database.py
"""

import sqlite3
import pandas as pd
import os
from pathlib import Path
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_paths():
    """Get project paths"""
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent
    
    return {
        'geo_csv': project_root / 'data' / 'Geography.csv',
        'soc_csv': project_root / 'data' / 'oes_soc_occs.csv',
        'alc_csv': project_root / 'data' / 'ALC_Export.csv',
        'db_path': project_root / 'data' / 'h1b_wages.db',
    }

def get_paths_to_save(file_requested):
    """Get project paths"""
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent
    
    path_dic = {
        'geo_csv': project_root / 'data' / 'processed_data_for_power_bi' / 'Geography.csv',
        'soc_csv': project_root / 'data' / 'processed_data_for_power_bi' / 'oes_soc_occs.csv',
        'alc_csv': project_root / 'data' / 'processed_data_for_power_bi' / 'ALC_Export.csv'
    }

    return path_dic[file_requested]

def verify_csv_files(paths):
    """Verify all CSV files exist"""
    logger.info("Verifying CSV files...")
    
    for csv_name, csv_path in paths.items():
        if csv_name.endswith('_csv'):
            if not csv_path.exists():
                raise FileNotFoundError(f"Missing: {csv_path}")
            logger.info(f"  ✓ Found {csv_path.name}")


def create_database(db_path):
    """Create new database and schema"""
    logger.info(f"\nCreating database at {db_path}...")
    
    # Remove old database if exists
    if db_path.exists():
        logger.warning(f"Database exists, removing old version...")
        db_path.unlink()
    
    # Ensure parent directory exists
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Connect to new database
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # ========== CREATE TABLES ==========
    logger.info("Creating tables...")
    
    # 1. Geography table
    cursor.execute('''
        CREATE TABLE geography (
            area_code TEXT PRIMARY KEY,
            state TEXT NOT NULL,
            county TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(state, county)
        )
    ''')
    cursor.execute('CREATE INDEX idx_geography_state ON geography(state)')
    cursor.execute('CREATE INDEX idx_geography_state_county ON geography(state, county)')
    logger.info("  ✓ Created geography table with indexes")
    
    # 2. Occupations table
    cursor.execute('''
        CREATE TABLE occupations (
            soc_code TEXT PRIMARY KEY,
            job_title TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('CREATE INDEX idx_occupations_title ON occupations(job_title)')
    cursor.execute('CREATE INDEX idx_occupations_soc ON occupations(soc_code)')
    logger.info("  ✓ Created occupations table with indexes")
    
    # 3. Wage levels table (depends on geography + occupations)
    cursor.execute('''
        CREATE TABLE wage_levels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            area_code TEXT NOT NULL,
            soc_code TEXT NOT NULL,
            l1_wage REAL NOT NULL,
            l2_wage REAL NOT NULL,
            l3_wage REAL NOT NULL,
            l4_wage REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(area_code, soc_code),
            FOREIGN KEY (area_code) REFERENCES geography(area_code),
            FOREIGN KEY (soc_code) REFERENCES occupations(soc_code)
        )
    ''')
    cursor.execute('CREATE INDEX idx_wage_levels_area_soc ON wage_levels(area_code, soc_code)')
    cursor.execute('CREATE INDEX idx_wage_levels_soc ON wage_levels(soc_code)')
    cursor.execute('CREATE INDEX idx_wage_levels_area ON wage_levels(area_code)')
    logger.info("  ✓ Created wage_levels table with indexes")
    
    # 4. Metadata table
    cursor.execute('''
        CREATE TABLE metadata (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    logger.info("  ✓ Created metadata table")
    
    conn.commit()
    return conn


def load_geography_data(conn, csv_path):
    """Load Geography.csv into database"""
    logger.info("\nLoading Geography.csv...")
    
    geo_df = pd.read_csv(str(csv_path))
    logger.info(f"  ✓ Read {len(geo_df)} rows from CSV")
    
    # Drop some columns and rename to lowercase
    geo_df['state'] = geo_df['State'].str.cat(geo_df['StateAb'], sep=' (') + ')'
    geo_df.drop(columns=["StateAb","State"], inplace=True)
    geo_df.rename(columns={
        "Area": 'area_code',
        "AreaName": 'area_name',
        "CountyTownName": 'county'
    }, inplace=True)    

    # Load into database
    geo_df.to_sql('geography', conn, if_exists='replace', index=False)
    logger.info(f"  ✓ Inserted {len(geo_df)} geography records")

    geo_df.to_csv(get_paths_to_save('geo_csv'), index=False, encoding="utf-8")
    
    return len(geo_df)


def load_occupations_data(conn, csv_path):
    """Load oes_soc_occs.csv into database"""
    logger.info("\nLoading oes_soc_occs.csv...")
    
    soc_df = pd.read_csv(str(csv_path))
    logger.info(f"  ✓ Read {len(soc_df)} rows from CSV")
    
    # Rename columns to lowercase
    soc_df.rename(columns={
        "soccode": 'soc_code',
        "Title": 'job_title',
        "Description": 'description'
    }, inplace=True)
    
    # Load into database
    soc_df.to_sql('occupations', conn, if_exists='replace', index=False)
    logger.info(f"  ✓ Inserted {len(soc_df)} occupation records")

    soc_df.to_csv(get_paths_to_save('soc_csv'), index=False, encoding="utf-8")
    
    return len(soc_df)


def load_wage_levels_data(conn, csv_path):
    """Load ALC_Export.csv into database"""
    logger.info("\nLoading ALC_Export.csv...")
    
    alc_df = pd.read_csv(str(csv_path))
    logger.info(f"  ✓ Read {len(alc_df)} rows from CSV")
    
    # Filter unwanted wage labels and convert hourly wage levels to annual salaries
    alc_df.query("Label != 'High Wage' and Label != 'No Leveled Wage'", inplace=True)

    cols = ['Level1', 'Level2', 'Level3', 'Level4']
    mask = alc_df['Label'].isna()
    alc_df.loc[mask, cols] = alc_df.loc[mask, cols] * 40 * 52

    alc_df.drop(columns="Label", inplace=True)
    
    # Rename columns to lowercase
    alc_df.rename(columns={
        "Area": 'area_code',
        "SocCode": 'soc_code',
        "GeoLvl": 'geo_level_wage',
        "Level1": 'l1_wage',
        "Level2": 'l2_wage',
        "Level3": 'l3_wage',
        "Level4": 'l4_wage',
        "Average": 'average'
    }, inplace=True)
    
    # Convert wage columns to float
    for col in ['l1_wage', 'l2_wage', 'l3_wage', 'l4_wage']:
        alc_df[col] = pd.to_numeric(alc_df[col], errors='coerce')
    
    # Load into database
    alc_df.to_sql('wage_levels', conn, if_exists='replace', index=False)
    logger.info(f"  ✓ Inserted {len(alc_df)} wage level records")

    alc_df.to_csv(get_paths_to_save('alc_csv'), index=False, encoding="utf-8")
    
    return len(alc_df)


def load_metadata(conn, geo_count, soc_count, alc_count):
    """Load metadata into database"""
    logger.info("\nInserting metadata...")
    
    cursor = conn.cursor()
    metadata = [
        ('last_import', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
        ('data_version', '2025-Q1'),
        ('total_counties', str(cursor.execute('SELECT COUNT(DISTINCT county) FROM geography').fetchone()[0])),
        ('total_occupations', str(soc_count)),
        ('total_wage_records', str(alc_count)),
    ]
    
    cursor.executemany('INSERT INTO metadata (key, value) VALUES (?, ?)', metadata)
    conn.commit()
    logger.info(f"  ✓ Inserted {len(metadata)} metadata records")


def verify_database(db_path):
    """Verify database creation and data integrity"""
    logger.info("\n" + "="*60)
    logger.info("DATABASE VERIFICATION")
    logger.info("="*60)
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Check table existence
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    logger.info(f"\nTables created: {', '.join(tables)}")
    
    # Check record counts
    cursor.execute('SELECT COUNT(*) FROM geography')
    geo_count = cursor.fetchone()[0]
    logger.info(f"  Geography records: {geo_count:,}")
    
    cursor.execute('SELECT COUNT(*) FROM occupations')
    occ_count = cursor.fetchone()[0]
    logger.info(f"  Occupations records: {occ_count:,}")
    
    cursor.execute('SELECT COUNT(*) FROM wage_levels')
    wage_count = cursor.fetchone()[0]
    logger.info(f"  Wage level records: {wage_count:,}")
    
    # Check database file size
    db_size_mb = db_path.stat().st_size / 1024 / 1024
    logger.info(f"\nDatabase file size: {db_size_mb:.2f} MB")
    
    # Sample data verification
    logger.info("\nSample data verification:")
    
    cursor.execute('SELECT state FROM geography LIMIT 5')
    states = [row[0] for row in cursor.fetchall()]
    logger.info(f"  Sample states: {', '.join(states)}")
    
    cursor.execute('SELECT soc_code, job_title FROM occupations LIMIT 3')
    for soc, title in cursor.fetchall():
        logger.info(f"    {soc}: {title}")
    
    cursor.execute('SELECT state, county, l1_wage FROM geography g JOIN wage_levels w ON g.area_code = w.area_code LIMIT 3')
    for state, county, wage in cursor.fetchall():
        logger.info(f"    {state}/{county}: L1 = ${wage:,.2f}")
    
    conn.close()
    
    logger.info("\n✓ Database verification complete!")
    return {
        'geo_count': geo_count,
        'occ_count': occ_count,
        'wage_count': wage_count,
        'db_size_mb': db_size_mb
    }


def main():
    """Main setup process"""
    logger.info("="*60)
    logger.info("H1B WAGE DASHBOARD - DATABASE SETUP")
    logger.info("="*60)
    
    try:
        # Get paths
        paths = get_paths()
        logger.info(f"\nProject root: {paths['db_path'].parent.parent.parent}")
        
        # Verify CSV files
        verify_csv_files(paths)
        
        # Create database and schema
        conn = create_database(paths['db_path'])
        
        # Load data
        geo_count = load_geography_data(conn, paths['geo_csv'])
        soc_count = load_occupations_data(conn, paths['soc_csv'])
        alc_count = load_wage_levels_data(conn, paths['alc_csv'])
        
        # Load metadata
        load_metadata(conn, geo_count, soc_count, alc_count)
        
        conn.close()
        
        # Verify
        stats = verify_database(paths['db_path'])
        
        logger.info("\n" + "="*60)
        logger.info("✓ DATABASE SETUP COMPLETE!")
        logger.info("="*60)
        logger.info(f"\nDatabase location: {paths['db_path']}")
        
        return True
        
    except Exception as e:
        logger.error(f"\n✗ DATABASE SETUP FAILED!")
        logger.error(f"Error: {e}", exc_info=True)
        return False


if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
