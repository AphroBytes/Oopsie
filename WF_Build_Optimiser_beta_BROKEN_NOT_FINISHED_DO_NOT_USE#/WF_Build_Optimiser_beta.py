import itertools
import json
import re
import requests
from bs4 import BeautifulSoup
from functools import lru_cache
from typing import Dict, List, Tuple

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from sqlalchemy import create_engine, Column, String, Integer, Float, PickleType
from sqlalchemy.orm import sessionmaker, declarative_base

# Setting up the Base for SQLAlchemy models
Base = declarative_base()

# Constants for API Endpoints
API_BASE_URL = 'https://warframe.fandom.com/api.php'
SNEKW_API_BASE_URL = 'https://wf.snekw.com/'

# SQLite Database Setup
DATABASE_URL = 'sqlite:///warframe_data.db'
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()


# Database Models
class WarframeModel(Base):
    __tablename__ = 'warframes'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    base_health = Column(Integer)
    base_armor = Column(Integer)
    base_energy = Column(Integer)
    base_shield = Column(Integer)
    base_sprint_speed = Column(Float)
    mod_polarity = Column(PickleType)


class WeaponModel(Base):
    __tablename__ = 'weapons'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    base_damage = Column(Float)
    base_crit_chance = Column(Float)
    base_crit_mult = Column(Float)
    base_status_chance = Column(Float)
    base_fire_rate = Column(Float)
    base_magazine_size = Column(Integer)
    damage_type = Column(String)
    mod_polarity = Column(PickleType)


class ModModel(Base):
    __tablename__ = 'mods'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    mod_type = Column(String)
    polarity = Column(String)
    rank = Column(Integer)
    max_rank = Column(Integer)
    stats = Column(PickleType)


# Data Structures
class Warframe:
    def __init__(self, name: str, base_health: int, base_armor: int, base_energy: int, base_shield: int, base_sprint_speed: float, mod_polarity: List[str], **kwargs):
        self.name = name
        self.base_health = base_health
        self.base_armor = base_armor
        self.base_energy = base_energy
        self.base_shield = base_shield
        self.base_sprint_speed = base_sprint_speed
        self.mod_polarity = mod_polarity
        self.__dict__.update(kwargs)


class Weapon:
    def __init__(self, name: str, base_damage: float, base_crit_chance: float, base_crit_mult: float, base_status_chance: float, base_fire_rate: float, base_magazine_size: int, damage_type: str, mod_polarity: List[str], **kwargs):
        self.name = name
        self.base_damage = base_damage
        self.base_crit_chance = base_crit_chance
        self.base_crit_mult = base_crit_mult
        self.base_status_chance = base_status_chance
        self.base_fire_rate = base_fire_rate
        self.base_magazine_size = base_magazine_size
        self.damage_type = damage_type
        self.mod_polarity = mod_polarity
        self.__dict__.update(kwargs)


class Mod:
    def __init__(self, name: str, mod_type: str, polarity: str, rank: int = 0, max_rank: int = 10, **kwargs):
        self.name = name
        self.mod_type = mod_type
        self.polarity = polarity
        self.rank = rank
        self.max_rank = max_rank
        self.__dict__.update(kwargs)

    def get_ranked_stats(self, rank: int) -> Dict:
        if rank > self.max_rank:
            rank = self.max_rank
        scaling_factor = rank / self.max_rank
        ranked_stats = {}
        for stat_name, stat_value in self.__dict__.items():
            if isinstance(stat_value, (int, float)):
                ranked_stats[stat_name] = stat_value * scaling_factor
        return ranked_stats

    def get_description(self):
        description = f"**{self.name}**\n" \
                      f"**Type:** {self.mod_type}\n" \
                      f"**Polarity:** {self.polarity}\n"
        for stat_name, stat_value in self.__dict__.items():
            if isinstance(stat_value, (int, float)):
                description += f"{stat_name}: {stat_value}\n"
        return description


class Enemy:
    def __init__(self, name: str, faction: str, level: int, damage_types: List[str], armor: int, shield: int, **kwargs):
        self.name = name
        self.faction = faction
        self.level = level
        self.damage_types = damage_types
        self.armor = armor
        self.shield = shield
        self.__dict__.update(kwargs)


# API Functions
def fetch_wiki_data(action: str, **params) -> Dict:
    params['action'] = action
    params['format'] = 'json'
    try:
        response = requests.get(API_BASE_URL, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching data from Warframe Wiki: {e}")
        return {}


def fetch_snekw_data(endpoint: str) -> Dict:
    try:
        response = requests.get(SNEKW_API_BASE_URL + endpoint)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching data from Snekw API: {e}")
        return {}


# Data Extraction Functions
def extract_warframe_data(warframe_name: str) -> Dict:
    try:
        data = fetch_wiki_data(action='parse', page=warframe_name, prop='wikitext')
        soup = BeautifulSoup(data['parse']['wikitext']['*'], 'html.parser')
        warframe_data = {}
        table = soup.find('table', class_='wikitable')
        if table is None:
            return {}

        for row in table.find_all('tr'):
            cells = row.find_all('td')
            if len(cells) >= 2:
                key = cells[0].text.strip()
                value = cells[1].text.strip()
                if key in ['Health', 'Armor', 'Shield', 'Energy']:
                    warframe_data[f'base_{key.lower()}'] = int(value.replace(',', ''))
                elif key == 'Polarities':
                    warframe_data['mod_polarity'] = [x.strip() for x in value.split(',')]
        return warframe_data
    except Exception as e:
        st.error(f"Error extracting Warframe data for '{warframe_name}': {e}")
        return {}


def extract_weapon_data(weapon_name: str) -> Dict:
    try:
        data = fetch_wiki_data(action='parse', page=weapon_name, prop='wikitext')
        soup = BeautifulSoup(data['parse']['wikitext']['*'], 'html.parser')
        weapon_data = {}
        table = soup.find('table', class_='wikitable')
        if table is None:
            return {}

        for row in table.find_all('tr'):
            cells = row.find_all('td')
            if len(cells) >= 2:
                key = cells[0].text.strip()
                value = cells[1].text.strip()
                if key == 'Damage':
                    damage_parts = value.split()
                    weapon_data['base_damage'] = float(damage_parts[0])
                    weapon_data['damage_type'] = damage_parts[1]
                elif key in ['Crit Chance', 'Crit Multiplier', 'Status Chance', 'Fire Rate']:
                    weapon_data[f'base_{key.replace(" ", "_").lower()}'] = float(value.strip('%').replace('x', '')) / (1 if key != 'Crit Chance' else 100)
                elif key == 'Magazine Size':
                    weapon_data['base_magazine_size'] = int(value.replace(',', ''))
                elif key == 'Polarities':
                    weapon_data['mod_polarity'] = [x.strip() for x in value.split(',')]
        return weapon_data
    except Exception as e:
        st.error(f"Error extracting Weapon data for '{weapon_name}': {e}")
        return {}


def extract_mod_data(mod_name: str) -> Dict:
    try:
        data = fetch_wiki_data(action='parse', page=mod_name, prop='wikitext')
        soup = BeautifulSoup(data['parse']['wikitext']['*'], 'html.parser')
        mod_data = {}
        table = soup.find('table', class_='wikitable')
        if table is None:
            return {}

        for row in table.find_all('tr'):
            cells = row.find_all('td')
            if len(cells) >= 2:
                key = cells[0].text.strip()
                value = cells[1].text.strip()
                if key == 'Type':
                    mod_data['mod_type'] = value
                elif key == 'Polarity':
                    mod_data['polarity'] = value
                elif key == 'Max Rank':
                    mod_data['max_rank'] = int(value)
                elif key == 'Stats':
                    stats = [x.strip() for x in value.split() if x.strip()]
                    mod_data['stats'] = {
                        stats[i]: stats[i + 1] for i in range(0, len(stats), 2) if i + 1 < len(stats)
                    }
        return mod_data
    except Exception as e:
        st.error(f"Error extracting Mod data for '{mod_name}': {e}")
        return {}


def extract_enemy_data(enemy_name: str) -> Dict:
    """Retrieves enemy data from the Warframe.fandom API.

    Args:
        enemy_name: The name of the enemy.

    Returns:
        A dictionary containing enemy data, or None if no data is found.
    """
    try:
        data = fetch_wiki_data(action='parse', page=enemy_name, prop='wikitext')
        soup = BeautifulSoup(data['parse']['wikitext']['*'], 'html.parser')
        enemy_data = {}

        health_table = soup.find('table', class_='infobox')
        if health_table:
            health_row = health_table.find('tr', string='Health')
            armor_row = health_table.find('tr', string='Armor')
            shield_row = health_table.find('tr', string='Shields')
            if health_row:
                enemy_data['Health'] = health_row.find_next_sibling('td').text.strip()
            if shield_row:
                enemy_data['Shields'] = shield_row.find_next_sibling('td').text.strip()
            if armor_row:
                enemy_data['Armor'] = armor_row.find_next_sibling('td').text.strip()

        weaknesses_section = soup.find('h3', string='Weaknesses')
        if weaknesses_section:
            weaknesses = [weakness.text.strip() for weakness in weaknesses_section.find_next_sibling('ul').find_all('li')]
            enemy_data['Weaknesses'] = weaknesses

        return enemy_data
    except Exception as e:
        st.error(f"Error fetching enemy data for '{enemy_name}': {e}")
        return {}


# Load Data from Wiki
@lru_cache(maxsize=None)
def load_data_from_wiki() -> Tuple[Dict[str, Dict], Dict[str, Dict], List[Mod]]:
    """Loads data from Warframe.fandom API and returns Warframes, Weapons, and Mods.

    Returns:
        A tuple containing dictionaries of Warframes and Weapons and a list of Mods.
    """
    warframes, weapons, mods = {}, {}, []
    try:
        warframe_names = fetch_snekw_data('warframes')['warframes']
        weapon_names = fetch_snekw_data('weapons')['weapons']
        mod_names = fetch_snekw_data('mods')['mods']

        for name in warframe_names:
            data = extract_warframe_data(name)
            if data:
                warframes[name] = data

        for name in weapon_names:
            data = extract_weapon_data(name)
            if data:
                weapons[name] = data

        for name in mod_names:
            data = extract_mod_data(name)
            if data:
                stats = {k: float(v) if '%' not in v else float(v.strip('%')) / 100 for k, v in
                         (data['stats'] or {}).items()}
                mods.append(Mod(name=name, mod_type=data['mod_type'], polarity=data['polarity'], max_rank=data['max_rank'], **stats))

        return warframes, weapons, mods
    except Exception as e:
        st.error(f"Error loading data from Warframe Wiki: {e}")
        return {}, {}, []


def populate_database():
    """Populates the database with data from the Warframe.fandom API."""
    try:
        warframes, weapons, mods = load_data_from_wiki()

        # Populate Warframe table
        for name, data in warframes.items():
            session.add(WarframeModel(
                name=name,
                base_health=data['base_health'],
                base_armor=data['base_armor'],
                base_energy=data['base_energy'],
                base_shield=data['base_shield'],
                base_sprint_speed=data.get('base_sprint_speed', 0),  # Defaulting sprint speed to 0 if unavailable
                mod_polarity=data['mod_polarity']
            ))

        # Populate Weapon table
        for name, data in weapons.items():
            session.add(WeaponModel(
                name=name,
                base_damage=data['base_damage'],
                base_crit_chance=data['base_crit_chance'],
                base_crit_mult=data['base_crit_mult'],
                base_status_chance=data['base_status_chance'],
                base_fire_rate=data['base_fire_rate'],
                base_magazine_size=data['base_magazine_size'],
                damage_type=data['damage_type'],
                mod_polarity=data['mod_polarity']
            ))

        # Populate Mod table
        for mod in mods:
            session.add(ModModel(
                name=mod.name,
                mod_type=mod.mod_type,
                polarity=mod.polarity,
                rank=mod.rank,
                max_rank=mod.max_rank,
                stats={stat_name: stat_value for stat_name, stat_value in mod.__dict__.items() if isinstance(stat_value, (int, float))}
            ))

        session.commit()
    except Exception as e:
        st.error(f"Error populating database: {e}")


def load_data_from_database() -> Tuple[Dict[str, Dict], Dict[str, Dict], List[Mod]]:
    """Loads data from the database."""
    try:
        warframes = {row.name: {
            'base_health': row.base_health,
            'base_armor': row.base_armor,
            'base_energy': row.base_energy,
            'base_shield': row.base_shield,
            'base_sprint_speed': row.base_sprint_speed,
            'mod_polarity': row.mod_polarity
        } for row in session.query(WarframeModel).all()}

        weapons = {row.name: {
            'base_damage': row.base_damage,
            'base_crit_chance': row.base_crit_chance,
            'base_crit_mult': row.base_crit_mult,
            'base_status_chance': row.base_status_chance,
            'base_fire_rate': row.base_fire_rate,
            'base_magazine_size': row.base_magazine_size,
            'damage_type': row.damage_type,
            'mod_polarity': row.mod_polarity
        } for row in session.query(WeaponModel).all()}

        mods = [Mod(
            name=row.name,
            mod_type=row.mod_type,
            polarity=row.polarity,
            rank=row.rank,
            max_rank=row.max_rank,
            **{stat_name: stat_value for stat_name, stat_value in row.stats.items()}
        ) for row in session.query(ModModel).all()]

        return warframes, weapons, mods
    except Exception as e:
        st.error(f"Error loading data from database: {e}")
        return {}, {}, []


# Initialize the database if not populated
if not session.query(WarframeModel).first():
    populate_database()

# Load data from the database
warframes, weapons, mods = load_data_from_database()

# Streamlit application title
st.title("Warframe Build Optimizer")

# Warframe and Weapon Selection
selected_warframe_name = st.selectbox("Select Warframe", list(warframes.keys()))
selected_warframe = Warframe(**warframes[selected_warframe_name])
selected_weapon_name = st.selectbox("Select Weapon", list(weapons.keys()))
selected_weapon = Weapon(**weapons[selected_weapon_name])

# Mod Selection
st.subheader("Mod Selection")
available_mods = st.multiselect("Select Mods", [mod.name for mod in mods], default=[], help="Select the mods you want to consider for your build.")
selected_mods = [mod for mod in mods if mod.name in available_mods]

# Mod Rank and Enemy Stats
mod_rank = st.slider("Mod Rank", 1, 10, 10)
target_armor = st.number_input("Target Enemy Armor", 0)
target_shield = st.number_input("Target Enemy Shield", 0)

# Optimization Objective
objective = st.radio("Optimization Objective", ["Damage", "Survivability"])

# Build Optimization and Results
if st.button("Optimize"):
    if not check_mod_polarity_match(selected_warframe, selected_weapon, selected_mods):
        st.warning("Warning: Mod polarities do not match Warframe/Weapon restrictions.", icon="⚠️")
    else:
        num_mods = len(selected_mods)
        if objective == "Damage":
            best_value, best_mods = find_optimal_mods(selected_warframe, selected_weapon, selected_mods, num_mods, objective, rank=mod_rank, target_armor=target_armor, target_shield=target_shield)
            st.subheader("Optimal Damage Build:")
            st.write(f"Best Damage: {best_value:.2f}")
            st.write(f"Mods: {best_mods}")
        else:
            best_value, best_mods = find_optimal_mods(selected_warframe, selected_weapon, selected_mods, num_mods, objective, rank=mod_rank)
            advanced_survivability = calculate_advanced_survivability(selected_warframe, best_mods, rank=mod_rank)
            st.subheader("Optimal Survivability Build:")
            st.write(f"Best Survivability Score: {best_value}")
            st.write(f"Mods: {best_mods}")
            st.write(f"Advanced Survivability Score: {advanced_survivability:.2f}")

    # Display Mod Descriptions
    st.subheader("Mod Descriptions")
    for mod in best_mods:
        st.write(mod.get_description())

    # Visualize Build Performance
    if st.button("Visualize Build"):
        visualize_build(selected_warframe, selected_weapon, selected_mods, rank=mod_rank, enemy_armor=target_armor, enemy_shield=target_shield)

# Mod Polarity Visualization
st.subheader("Mod Polarity Visualization")
warframe_polarities = selected_warframe.mod_polarity
weapon_polarities = selected_weapon.mod_polarity
mod_polarities = [mod.polarity for mod in selected_mods]

st.write("Warframe Polarities:", warframe_polarities)
st.write("Weapon Polarities:", weapon_polarities)
st.write("Selected Mod Polarities:", mod_polarities)

# Enemy Information
st.subheader("Enemy Information")
enemy_name = st.text_input("Enemy Name", "Example Enemy")
enemy_faction = st.selectbox("Enemy Faction", ["Grineer", "Corpus", "Infested", "Sentient", "Orokin", "Tenno"])
enemy_level = st.number_input("Enemy Level", 1, 100, 1)

# Get Enemy Data
enemy_data = extract_enemy_data(enemy_name)
if enemy_data:
    enemy = Enemy(**enemy_data)
else:
    enemy = Enemy(name=enemy_name, faction=enemy_faction, level=enemy_level,
                   damage_types=["Impact", "Puncture", "Slash"], armor=target_armor, shield=target_shield)

# Enemy Details Display
st.write("Enemy Details:")
st.write(f"Name: {enemy.name}")
st.write(f"Faction: {enemy.faction}")
st.write(f"Level: {enemy.level}")
st.write(f"Armor: {enemy.armor}")
st.write(f"Shield: {enemy.shield}")
st.write(f"Damage Types: {enemy.damage_types}")

# Warframe Stats Display
st.write("Warframe Stats:")
st.write(f"Name: {selected_warframe.name}")
st.write(f"Health: {selected_warframe.base_health}")
st.write(f"Armor: {selected_warframe.base_armor}")
st.write(f"Energy: {selected_warframe.base_energy}")
st.write(f"Shield: {selected_warframe.base_shield}")

# Advanced Build Visualization
st.subheader("Advanced Build Visualization")
# Display the enemy details and the selected Warframe's stats
st.write("Enemy Details:")
st.write(f"Name: {enemy.name}")
st.write(f"Faction: {enemy.faction}")
st.write(f"Level: {enemy.level}")
st.write(f"Armor: {enemy.armor}")
st.write(f"Shield: {enemy.shield}")
st.write(f"Damage Types: {enemy.damage_types}")

st.write("Warframe Stats:")
st.write(f"Name: {selected_warframe.name}")
st.write(f"Health: {selected_warframe.base_health}")
st.write(f"Armor: {selected_warframe.base_armor}")
st.write(f"Energy: {selected_warframe.base_energy}")
st.write(f"Shield: {selected_warframe.base_shield}")

# Visualization options
st.write("Visualization Options:")
# Bar chart visualizing different characteristics
def bar_chart_warframe_vs_enemy(warframe: Warframe, enemy: Enemy):
    categories = ['Health', 'Armor', 'Shield']
    warframe_stats = [warframe.base_health, warframe.base_armor, warframe.base_shield]
    enemy_stats = [enemy.shield, enemy.armor, enemy.shield]  # Assuming enemy structure has required stats

    bar_width = 0.35
    index = range(len(categories))

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(index, warframe_stats, bar_width, label='Warframe')
    ax.bar([i + bar_width for i in index], enemy_stats, bar_width, label='Enemy')
    ax.set_xlabel('Stats')
    ax.set_title('Warframe Stats vs Enemy Stats')
    ax.set_xticks([i + bar_width / 2 for i in index])
    ax.set_xticklabels(categories)
    ax.legend()

    return fig

st.pyplot(bar_chart_warframe_vs_enemy(selected_warframe, enemy))

# User Feedback and Data Collection
st.subheader("User Feedback and Data Collection")
user_feedback = st.text_area("Comments or Suggestions", "Enter your feedback here...")
if st.button("Submit Feedback"):
    # Save feedback or display message (to be implemented)
    st.success("Thank you for your feedback!")


# Calculation Functions
def calculate_damage(weapon: Weapon, mods: List[Mod], rank: int = 10, target_armor: int = 0, target_shield: int = 0) -> Tuple[float, float, float, float]:
    damage = weapon.base_damage
    crit_chance = weapon.base_crit_chance
    crit_mult = weapon.base_crit_mult
    status_chance = weapon.base_status_chance

    for mod in mods:
        ranked_stats = mod.get_ranked_stats(rank)
        damage += ranked_stats.get("damage", 0)
        crit_chance += ranked_stats.get("crit_chance", 0)
        crit_mult += ranked_stats.get("crit_mult", 0)
        status_chance += ranked_stats.get("status_chance", 0)

    damage_type_modifier = {
        "Impact": 1.25 * (1 - 0.25 * (target_shield / (target_shield + 300))),
        "Puncture": 1.25 * (1 - 0.25 * (target_armor / (target_armor + 300))),
        "Slash": 1 + (0.25 * (target_shield / (target_shield + 300))),
    }.get(weapon.damage_type, 1)

    damage *= damage_type_modifier

    status_effects = [mod.mod_type for mod in mods if mod.mod_type == "Status"]
    if "Viral" in status_effects and "Heat" in status_effects:
        damage *= 1.5 

    return damage, crit_chance, crit_mult, status_chance


def calculate_survivability(warframe: Warframe, mods: List[Mod], rank: int = 10) -> Tuple[int, int, int, int]:
    armor = warframe.base_armor
    energy = warframe.base_energy
    shield = warframe.base_shield
    health = warframe.base_health

    for mod in mods:
        ranked_stats = mod.get_ranked_stats(rank)
        armor += ranked_stats.get("armor", 0)
        energy += ranked_stats.get("energy", 0)
        shield += ranked_stats.get("shield", 0)
        health += ranked_stats.get("health", 0)

    return armor, energy, shield, health


def find_optimal_mods(warframe: Warframe, weapon: Weapon, mods: List[Mod], num_mods: int, objective: str = "damage", rank: int = 10, target_armor: int = 0, target_shield: int = 0) -> Tuple[float, List[Mod]]:
    mod_combinations = list(itertools.combinations(mods, num_mods))

    if objective == "damage":
        best_value = 0
    elif objective == "survivability":
        best_value = 0
    else:
        raise ValueError("Invalid optimization objective.")
    
    best_mods = None

    for combination in mod_combinations:
        if objective == "damage":
            damage, _, _, _ = calculate_damage(weapon, combination, rank, target_armor, target_shield)
            if damage > best_value:
                best_value = damage
                best_mods = combination
        elif objective == "survivability":
            armor, energy, shield, health = calculate_survivability(warframe, combination, rank)
            survivability_score = armor + energy + shield + health
            if survivability_score > best_value:
                best_value = survivability_score
                best_mods = combination

    return best_value, best_mods


import itertools
import json
import re
import requests
from bs4 import BeautifulSoup
from functools import lru_cache
from typing import Dict, List, Tuple

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from sqlalchemy import create_engine, Column, String, Integer, Float, PickleType
from sqlalchemy.orm import sessionmaker, declarative_base

# Setting up the Base for SQLAlchemy models
Base = declarative_base()

# Constants for API Endpoints
API_BASE_URL = 'https://warframe.fandom.com/api.php'
SNEKW_API_BASE_URL = 'https://wf.snekw.com/'

# SQLite Database Setup
DATABASE_URL = 'sqlite:///warframe_data.db'
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

# Database Models
class WarframeModel(Base):
    __tablename__ = 'warframes'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    base_health = Column(Integer)
    base_armor = Column(Integer)
    base_energy = Column(Integer)
    base_shield = Column(Integer)
    base_sprint_speed = Column(Float)
    mod_polarity = Column(PickleType)

class WeaponModel(Base):
    __tablename__ = 'weapons'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    base_damage = Column(Float)
    base_crit_chance = Column(Float)
    base_crit_mult = Column(Float)
    base_status_chance = Column(Float)
    base_fire_rate = Column(Float)
    base_magazine_size = Column(Integer)
    damage_type = Column(String)
    mod_polarity = Column(PickleType)

class ModModel(Base):
    __tablename__ = 'mods'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    mod_type = Column(String)
    polarity = Column(String)
    rank = Column(Integer)
    max_rank = Column(Integer)
    stats = Column(PickleType)

# Extractor Functions
def fetch_data(url: str, params: Dict = None) -> Dict:
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching data: {e}")
        return {}

def extract_data_from_wiki(action: str, **params) -> Dict:
    params['action'] = action
    params['format'] = 'json'
    return fetch_data(API_BASE_URL, params)

# Extract Warframe Data
def extract_warframe_data(warframe_name: str) -> Dict:
    data = extract_data_from_wiki('parse', page=warframe_name, prop='wikitext')
    soup = BeautifulSoup(data['parse']['wikitext']['*'], 'html.parser')
    warframe_data = {}
    table = soup.find('table', class_='wikitable')
    
    for row in table.find_all('tr'):
        cells = row.find_all('td')
        if len(cells) >= 2:
            key = cells[0].text.strip()
            value = cells[1].text.strip()
            if key in ['Health', 'Armor', 'Shield', 'Energy']:
                warframe_data[f'base_{key.lower()}'] = int(value.replace(',', ''))
            elif key == 'Polarities':
                warframe_data['mod_polarity'] = [x.strip() for x in value.split(',')]
    return warframe_data

# Extract Weapon Data
def extract_weapon_data(weapon_name: str) -> Dict:
    data = extract_data_from_wiki('parse', page=weapon_name, prop='wikitext')
    soup = BeautifulSoup(data['parse']['wikitext']['*'], 'html.parser')
    weapon_data = {}
    
    table = soup.find('table', class_='wikitable')
    for row in table.find_all('tr'):
        cells = row.find_all('td')
        if len(cells) >= 2:
            key = cells[0].text.strip()
            value = cells[1].text.strip()
            if key == 'Damage':
                damage_parts = value.split()
                weapon_data['base_damage'] = float(damage_parts[0])
                weapon_data['damage_type'] = damage_parts[1]
            elif key in ['Crit Chance', 'Crit Multiplier', 'Status Chance', 'Fire Rate']:
                weapon_data[f'base_{key.replace(" ", "_").lower()}'] = float(value.strip('%').replace('x', '')) / (100 if key == 'Crit Chance' else 1)
            elif key == 'Magazine Size':
                weapon_data['base_magazine_size'] = int(value.replace(',', ''))
            elif key == 'Polarities':
                weapon_data['mod_polarity'] = [x.strip() for x in value.split(',')]
    return weapon_data

# Extract Mod Data
def extract_mod_data(mod_name: str) -> Dict:
    data = extract_data_from_wiki('parse', page=mod_name, prop='wikitext')
    soup = BeautifulSoup(data['parse']['wikitext']['*'], 'html.parser')
    mod_data = {}
    
    table = soup.find('table', class_='wikitable')
    for row in table.find_all('tr'):
        cells = row.find_all('td')
        if len(cells) >= 2:
            key = cells[0].text.strip()
            value = cells[1].text.strip()
            if key == 'Type':
                mod_data['mod_type'] = value
            elif key == 'Polarity':
                mod_data['polarity'] = value
            elif key == 'Max Rank':
                mod_data['max_rank'] = int(value)
            elif key == 'Stats':
                stats = re.split(r'\s*[\n,]\s*', value.strip())
                mod_data['stats'] = {stats[i]: float(stats[i + 1]) for i in range(0, len(stats), 2) if i + 1 < len(stats)}
    return mod_data

# Load Data from Wiki
@lru_cache(maxsize=None)
def load_data_from_wiki() -> Tuple[Dict[str, Dict], Dict[str, Dict], List[Mod]]:
    """Loads Warframes, Weapons and Mods data from the wiki."""
    warframes, weapons, mods = {}, {}, []
    try:
        warframe_names = fetch_data(f'{SNEKW_API_BASE_URL}warframes')['warframes']
        weapon_names = fetch_data(f'{SNEKW_API_BASE_URL}weapons')['weapons']
        mod_names = fetch_data(f'{SNEKW_API_BASE_URL}mods')['mods']

        for name in warframe_names:
            data = extract_warframe_data(name)
            if data:
                warframes[name] = data

        for name in weapon_names:
            data = extract_weapon_data(name)
            if data:
                weapons[name] = data

        for name in mod_names:
            data = extract_mod_data(name)
            if data:
                mod_instance = Mod(name=name, mod_type=data['mod_type'], polarity=data['polarity'], 
                                   max_rank=data['max_rank'], **data['stats'])
                mods.append(mod_instance)

        return warframes, weapons, mods
    except Exception as e:
        st.error(f"Error loading data from Warframe Wiki: {e}")
        return {}, {}, []

# Populate Database
def populate_database():
    """Populates the database with data from the Warframe.fandom API."""
    try:
        warframes, weapons, mods = load_data_from_wiki()

        # Populate Warframe table
        for name, data in warframes.items():
            session.add(WarframeModel(name=name, 
                                       base_health=data['base_health'], 
                                       base_armor=data['base_armor'], 
                                       base_energy=data['base_energy'], 
                                       base_shield=data['base_shield'], 
                                       base_sprint_speed=data.get('base_sprint_speed', 0),  # Defaulting sprint speed to 0 if unavailable
                                       mod_polarity=data['mod_polarity']))

        # Populate Weapon table
        for name, data in weapons.items():
            session.add(WeaponModel(name=name, 
                                     base_damage=data['base_damage'], 
                                     base_crit_chance=data['base_crit_chance'], 
                                     base_crit_mult=data['base_crit_mult'], 
                                     base_status_chance=data['base_status_chance'], 
                                     base_fire_rate=data['base_fire_rate'], 
                                     base_magazine_size=data['base_magazine_size'], 
                                     damage_type=data['damage_type'], 
                                     mod_polarity=data['mod_polarity']))

        # Populate Mod table
        for mod in mods:
            session.add(ModModel(name=mod.name,
                                 mod_type=mod.mod_type,
                                 polarity=mod.polarity,
                                 rank=mod.rank,
                                 max_rank=mod.max_rank,
                                 stats={stat_name: stat_value for stat_name, stat_value in mod.__dict__.items() if isinstance(stat_value, (int, float))}))

        session.commit()
    except Exception as e:
        st.error(f"Error populating database: {e}")

# Load Data from Database
def load_data_from_database() -> Tuple[Dict[str, Dict], Dict[str, Dict], List[Mod]]:
    """Loads data from the database."""
    warframes = {row.name: {
        'base_health': row.base_health,
        'base_armor': row.base_armor,
        'base_energy': row.base_energy,
        'base_shield': row.base_shield,
        'base_sprint_speed': row.base_sprint_speed,
        'mod_polarity': row.mod_polarity
    } for row in session.query(WarframeModel).all()}

    weapons = {row.name: {
        'base_damage': row.base_damage,
        'base_crit_chance': row.base_crit_chance,
        'base_crit_mult': row.base_crit_mult,
        'base_status_chance': row.base_status_chance,
        'base_fire_rate': row.base_fire_rate,
        'base_magazine_size': row.base_magazine_size,
        'damage_type': row.damage_type,
        'mod_polarity': row.mod_polarity
    } for row in session.query(WeaponModel).all()}

    mods = [Mod(name=row.name, mod_type=row.mod_type, polarity=row.polarity, 
                rank=row.rank, max_rank=row.max_rank, **row.stats) for row in session.query(ModModel).all()]

    return warframes, weapons, mods

# Check if Database Needs to be Populated
if not session.query(WarframeModel).first():
    populate_database()

# Load data from the database
warframes, weapons, mods = load_data_from_database()

# Streamlit application starts here
st.title("Warframe Build Optimizer")

# Warframe and Weapon Selection
selected_warframe_name = st.selectbox("Select Warframe", list(warframes.keys()))
selected_warframe = Warframe(**warframes[selected_warframe_name])
selected_weapon_name = st.selectbox("Select Weapon", list(weapons.keys()))
selected_weapon = Weapon(**weapons[selected_weapon_name])

# Mod Selection
st.subheader("Mod Selection")
available_mods = st.multiselect("Select Mods", [mod.name for mod in mods], default=[], help="Select the mods you want to consider for your build.")
selected_mods = [mod for mod in mods if mod.name in available_mods]

# Mod Rank and Enemy Stats
mod_rank = st.slider("Mod Rank", 1, 10, 10)
target_armor = st.number_input("Target Enemy Armor", 0)
target_shield = st.number_input("Target Enemy Shield", 0)

# Optimization Objective
objective = st.radio("Optimization Objective", ["Damage", "Survivability"])

# Perform Optimization
if st.button("Optimize"):
    if not check_mod_polarity_match(selected_warframe, selected_weapon, selected_mods):
        st.warning("Warning: Mod polarities do not match Warframe/Weapon restrictions.")
    else:
        best_value, best_mods = find_optimal_mods(selected_warframe, selected_weapon, selected_mods, 
                                                   len(selected_mods), objective, rank=mod_rank, 
                                                   target_armor=target_armor, target_shield=target_shield)
        st.subheader(f"Optimal {objective} Build:")
        st.write(f"Best Value: {best_value:.2f}")
        st.write(f"Mods: {best_mods}")

    # Display Mod Descriptions
    st.subheader("Mod Descriptions")
    for mod in best_mods:
        st.write(mod.get_description())

# Enemy Information
st.subheader("Enemy Information")
enemy_name = st.text_input("Enemy Name", "Example Enemy")
enemy_faction = st.selectbox("Enemy Faction", ["Grineer", "Corpus", "Infested", "Sentient", "Orokin", "Tenno"])
enemy_level = st.number_input("Enemy Level", 1, 100, 1)

# Get Enemy Data
enemy_data = extract_enemy_data(enemy_name)
if enemy_data:
    enemy = Enemy(**enemy_data)
else:
    enemy = Enemy(name=enemy_name, faction=enemy_faction, level=enemy_level,
                   damage_types=["Impact", "Puncture", "Slash"], armor=target_armor, shield=target_shield)

# Display Enemy Details
st.write("Enemy Details:")
st.write(f"Name: {enemy.name}")
st.write(f"Faction: {enemy.faction}")
st.write(f"Level: {enemy.level}")
st.write(f"Armor: {enemy.armor}")
st.write(f"Shield: {enemy.shield}")
st.write(f"Damage Types: {enemy.damage_types}")

# Warframe Stats Display
st.write("Warframe Stats:")
st.write(f"Name: {selected_warframe.name}")
st.write(f"Health: {selected_warframe.base_health}")
st.write(f"Armor: {selected_warframe.base_armor}")
st.write(f"Energy: {selected_warframe.base_energy}")
st.write(f"Shield: {selected_warframe.base_shield}")

# Bar Chart Visualization
def bar_chart_warframe_vs_enemy(warframe: Warframe, enemy: Enemy):
    categories = ['Health', 'Armor', 'Shield']
    warframe_stats = [warframe.base_health, warframe.base_armor, warframe.base_shield]
    enemy_stats = [enemy.shield, enemy.armor, enemy.shield]

    bar_width = 0.35
    index = range(len(categories))

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(index, warframe_stats, bar_width, label='Warframe')
    ax.bar([i + bar_width for i in index], enemy_stats, bar_width, label='Enemy')
    ax.set_xlabel('Stats')
    ax.set_title('Warframe Stats vs Enemy Stats')
    ax.set_xticks([i + bar_width / 2 for i in index])
    ax.set_xticklabels(categories)
    ax.legend()

    return fig

st.pyplot(bar_chart_warframe_vs_enemy(selected_warframe, enemy))

# Function to save feedback
def save_feedback(feedback):
    with open("user_feedback.txt", "a") as f:  # Append to feedback file
        f.write(feedback + "\n")

# User feedback and data collection section
st.subheader("User Feedback and Data Collection")
user_feedback = st.text_area("Comments or Suggestions", "Enter your feedback here...")

if st.button("Submit Feedback"):
    if user_feedback.strip():  # Check if feedback is not empty
        save_feedback(user_feedback)
        st.success("Thank you for your feedback!")
    else:
        st.error("Please enter some feedback before submitting.")

# Calculation Functions
def calculate_damage(weapon: Weapon, mods: List[Mod], rank: int = 10, target_armor: int = 0, target_shield: int = 0) -> Tuple[float, float, float, float]:
    damage = weapon.base_damage
    crit_chance = weapon.base_crit_chance
    crit_mult = weapon.base_crit_mult
    status_chance = weapon.base_status_chance

    for mod in mods:
        ranked_stats = mod.get_ranked_stats(rank)
        damage += ranked_stats.get("damage", 0)
        crit_chance += ranked_stats.get("crit_chance", 0)
        crit_mult += ranked_stats.get("crit_mult", 0)
        status_chance += ranked_stats.get("status_chance", 0)

    # Damage Type Modifier
    damage_type_modifier = {
        "Impact": 1.25 * (1 - 0.25 * (target_shield / (target_shield + 300))),
        "Puncture": 1.25 * (1 - 0.25 * (target_armor / (target_armor + 300))),
        "Slash": 1 + (0.25 * (target_shield / (target_shield + 300))),
    }.get(weapon.damage_type, 1)

    damage *= damage_type_modifier
    return damage, crit_chance, crit_mult, status_chance

def check_mod_polarity_match(warframe: Warframe, weapon: Weapon, mods: List[Mod]) -> bool:
    return all(mod.polarity in warframe.mod_polarity or mod.polarity in weapon.mod_polarity for mod in mods)

def find_optimal_mods(warframe: Warframe, weapon: Weapon, mods: List[Mod], num_mods: int, 
                       objective: str = "Damage", rank: int = 10, target_armor: int = 0, target_shield: int = 0) -> Tuple[float, List[Mod]]:
    mod_combinations = list(itertools.combinations(mods, num_mods))
    
    best_value = float('-inf') if objective == "Damage" else float('inf')
    best_mods = None

    for combination in mod_combinations:
        if objective == "Damage":
            damage, _, _, _ = calculate_damage(weapon, combination, rank, target_armor, target_shield)
            if damage > best_value:
                best_value = damage
                best_mods = combination
        elif objective == "Survivability":
            armor, energy, shield, health = calculate_survivability(warframe, combination, rank)
            survivability_score = armor + energy + shield + health
            if survivability_score > best_value:
                best_value = survivability_score
                best_mods = combination

    return best_value, best_mods

def check_mod_polarity_match(warframe: Warframe, weapon: Weapon, mods: List[Mod]) -> bool:
    # Create a set of valid polarities to speed up membership testing
    valid_polarities = set(warframe.mod_polarity) | set(weapon.mod_polarity)
    return all(mod.polarity in valid_polarities for mod in mods)


def calculate_advanced_survivability(warframe: Warframe, mods: List[Mod], rank: int = 10, enemy_damage_types: List[str] = None) -> float:
    enemy_damage_types = enemy_damage_types or ["Impact", "Puncture", "Slash"]
    armor, energy, shield, health = calculate_survivability(warframe, mods, rank)

    # Calculate energy efficiency
    energy_efficiency = 1 + (energy / warframe.base_energy)

    # Calculate damage type resistance by using a mapping
    resistance_map = {
        "Impact": armor,
        "Puncture": shield,
        "Slash": health
    }

    damage_type_resistance = sum(resistance_map.get(damage_type, 0) for damage_type in enemy_damage_types)

    # Return the advanced survivability score
    return (energy_efficiency * (shield + health + armor)) / len(enemy_damage_types)


def visualize_build(warframe: Warframe, weapon: Weapon, mods: List[Mod], rank: int = 10, enemy_armor: int = 0, enemy_shield: int = 0):
    try:
        damage_values = []
        survivability_values = []

        # Pre-calculate mod counts
        for mod_count in range(1, len(mods) + 1):
            best_damage, _ = find_optimal_mods(warframe, weapon, mods, mod_count, "damage", rank, enemy_armor, enemy_shield)
            damage_values.append(best_damage)

            best_survivability, _ = find_optimal_mods(warframe, weapon, mods, mod_count, "survivability", rank)
            survivability_values.append(best_survivability)

        # Performance Visualization with Bar Chart
        plt.figure(figsize=(14, 6))
        x_labels = range(1, len(mods) + 1)
        plt.bar(x_labels, damage_values, label="Damage", alpha=0.7)
        plt.bar(x_labels, survivability_values, label="Survivability", alpha=0.5)

        plt.xlabel("Number of Mods")
        plt.ylabel("Performance")
        plt.title("Build Performance with Increasing Mods")
        plt.legend()
        plt.tight_layout()
        st.pyplot(plt)
        
    except Exception as e:
        st.error(f"Error visualizing build: {e}")