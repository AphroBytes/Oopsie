import itertools
import json
import re
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from typing import Dict, List, Tuple, Optional
import math

import requests
from lxml import html
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from sqlalchemy import create_engine, Column, String, Integer, Float, PickleType, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from sqlalchemy.exc import SQLAlchemyError

# Constants
API_BASE_URL = 'https://warframe.fandom.com/api.php'
SNEKW_API_BASE_URL = 'https://wf.snekw.com/'
DATABASE_URL = 'sqlite:///warframe_data.db'

# SQLAlchemy setup
Base = declarative_base()
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

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
    abilities = relationship("AbilityModel", back_populates="warframe")

class AbilityModel(Base):
    __tablename__ = 'abilities'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    effects = Column(PickleType)
    warframe_id = Column(Integer, ForeignKey('warframes.id'))
    warframe = relationship("WarframeModel", back_populates="abilities")

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

class EnemyModel(Base):
    __tablename__ = 'enemies'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    faction = Column(String)
    base_level = Column(Integer)
    base_health = Column(Float)
    base_armor = Column(Float)
    base_shield = Column(Float)
    damage_types = Column(PickleType)

# Data Classes
class Ability:
    def __init__(self, name: str, effects: Dict[str, float]):
        self.name = name
        self.effects = effects

class Warframe:
    def __init__(self, name: str, base_health: int, base_armor: int, base_energy: int, base_shield: int, base_sprint_speed: float, mod_polarity: List[str], abilities: List[Ability], **kwargs):
        self.name = name
        self.base_health = base_health
        self.base_armor = base_armor
        self.base_energy = base_energy
        self.base_shield = base_shield
        self.base_sprint_speed = base_sprint_speed
        self.mod_polarity = mod_polarity
        self.abilities = abilities
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
        return {stat_name: stat_value * scaling_factor 
                for stat_name, stat_value in self.__dict__.items() 
                if isinstance(stat_value, (int, float))}

    def get_description(self) -> str:
        description = f"**{self.name}**
**Type:** {self.mod_type}
**Polarity:** {self.polarity}
"
        return description + "
".join(f"{stat_name}: {stat_value}" 
                                       for stat_name, stat_value in self.__dict__.items() 
                                       if isinstance(stat_value, (int, float)))

class Enemy:
    def __init__(self, name: str, faction: str, base_level: int, base_health: float, base_armor: float, base_shield: float, damage_types: List[str], **kwargs):
        self.name = name
        self.faction = faction
        self.base_level = base_level
        self.base_health = base_health
        self.base_armor = base_armor
        self.base_shield = base_shield
        self.damage_types = damage_types
        self.__dict__.update(kwargs)

    def scale_stats(self, level: int) -> Dict[str, float]:
        level_diff = level - self.base_level
        if level_diff <= 0:
            return {
                'health': self.base_health,
                'armor': self.base_armor,
                'shield': self.base_shield
            }
        
        health_mult = (1 + 0.015 * level_diff) ** 2
        armor_mult = (1 + 0.005 * level_diff) ** 1.75
        shield_mult = (1 + 0.0075 * level_diff) ** 2

        return {
            'health': self.base_health * health_mult,
            'armor': self.base_armor * armor_mult,
            'shield': self.base_shield * shield_mult
        }

# API Functions
@lru_cache(maxsize=128)
def fetch_api_data(url: str, params: Dict = None) -> Dict:
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching data from API: {e}")
        return {}

def fetch_wiki_data(action: str, **params) -> Dict:
    params.update({'action': action, 'format': 'json'})
    return fetch_api_data(API_BASE_URL, params)

def fetch_snekw_data(endpoint: str) -> Dict:
    return fetch_api_data(SNEKW_API_BASE_URL + endpoint)

# Data Extraction Functions
@lru_cache(maxsize=128)
def extract_warframe_data(warframe_name: str) -> Dict:
    try:
        data = fetch_wiki_data('parse', page=warframe_name, prop='wikitext')
        tree = html.fromstring(data['parse']['wikitext']['*'])
        table = tree.xpath('//table[@class="wikitable"]')[0]

        warframe_data = {}
        for row in table.xpath('.//tr'):
            cells = row.xpath('.//td')
            if len(cells) >= 2:
                key, value = cells[0].text_content().strip(), cells[1].text_content().strip()
                if key in ['Health', 'Armor', 'Shield', 'Energy']:
                    warframe_data[f'base_{key.lower()}'] = int(value.replace(',', ''))
                elif key == 'Sprint Speed':
                    warframe_data['base_sprint_speed'] = float(value)
                elif key == 'Polarities':
                    warframe_data['mod_polarity'] = [x.strip() for x in value.split(',')]
        
        warframe_data['abilities'] = extract_warframe_abilities(warframe_name)

        return warframe_data
    except Exception as e:
        st.error(f"Error extracting Warframe data for '{warframe_name}': {e}")
        return {}

@lru_cache(maxsize=128)
def extract_warframe_abilities(warframe_name: str) -> List[Ability]:
    try:
        data = fetch_wiki_data('parse', page=f"{warframe_name}/Abilities", prop='wikitext')
        tree = html.fromstring(data['parse']['wikitext']['*'])
        ability_sections = tree.xpath('//h2[contains(@class, "mw-headline")]')

        abilities = []
        for section in ability_sections:
            ability_name = section.text_content().strip()
            ability_table = section.xpath('following-sibling::table[@class="wikitable"][1]')[0]
            
            effects = {}
            for row in ability_table.xpath('.//tr'):
                cells = row.xpath('.//td')
                if len(cells) >= 2:
                    key, value = cells[0].text_content().strip().lower(), cells[1].text_content().strip()
                    effects[key] = parse_percentage(value)

            abilities.append(Ability(ability_name, effects))

        return abilities
    except Exception as e:
        st.error(f"Error extracting abilities for '{warframe_name}': {e}")
        return []

@lru_cache(maxsize=128)
def extract_weapon_data(weapon_name: str) -> Dict:
    try:
        data = fetch_wiki_data('parse', page=weapon_name, prop='wikitext')
        tree = html.fromstring(data['parse']['wikitext']['*'])
        table = tree.xpath('//table[@class="wikitable"]')[0]

        weapon_data = {}
        for row in table.xpath('.//tr'):
            cells = row.xpath('.//td')
            if len(cells) >= 2:
                key, value = cells[0].text_content().strip(), cells[1].text_content().strip()
                if key in ['Damage', 'Critical Chance', 'Critical Multiplier', 'Status Chance', 'Fire Rate']:
                    weapon_data[f'base_{key.lower().replace(" ", "_")}'] = float(value.strip('%').replace(',', ''))
                elif key == 'Magazine Size':
                    weapon_data['base_magazine_size'] = int(value)
                elif key == 'Damage Type':
                    weapon_data['damage_type'] = value
                elif key == 'Polarities':
                    weapon_data['mod_polarity'] = [x.strip() for x in value.split(',')]

        return weapon_data
    except Exception as e:
        st.error(f"Error extracting Weapon data for '{weapon_name}': {e}")
        return {}

@lru_cache(maxsize=128)
def extract_mod_data(mod_name: str) -> Dict:
    try:
        data = fetch_wiki_data('parse', page=mod_name, prop='wikitext')
        tree = html.fromstring(data['parse']['wikitext']['*'])
        table = tree.xpath('//table[@class="wikitable"]')[0]

        mod_data = {}
        for row in table.xpath('.//tr'):
            cells = row.xpath('.//td')
            if len(cells) >= 2:
                key, value = cells[0].text_content().strip(), cells[1].text_content().strip()
                if key == 'Type':
                    mod_data['mod_type'] = value
                elif key == 'Polarity':
                    mod_data['polarity'] = value
                elif key == 'Rank':
                    mod_data['max_rank'] = int(value)
                else:
                    mod_data[key.lower()] = parse_percentage(value)

        return mod_data
    except Exception as e:
        st.error(f"Error extracting Mod data for '{mod_name}': {e}")
        return {}

@lru_cache(maxsize=128)
def extract_enemy_data(enemy_name: str) -> Dict:
    try:
        data = fetch_wiki_data('parse', page=enemy_name, prop='wikitext')
        tree = html.fromstring(data['parse']['wikitext']['*'])
        tables = tree.xpath('//table[@class="wikitable"]')
        
        if not tables:
            return {}

        table = tables[0]
        enemy_data = {
            'name': enemy_name,
            'faction': 'Unknown',
            'base_level': 1,
            'base_health': 100.0,
            'base_armor': 0.0,
            'base_shield': 0.0,
            'damage_types': []
        }

        for row in table.xpath('.//tr'):
            cells = row.xpath('.//td')
            if len(cells) >= 2:
                key, value = cells[0].text_content().strip(), cells[1].text_content().strip()
                if key in ['Health', 'Armor', 'Shield']:
                    enemy_data[f'base_{key.lower()}'] = float(value.replace(',', ''))
                elif key == 'Level':
                    enemy_data['base_level'] = int(value.split('-')[0])  # Use the lower bound of the level range
                elif key == 'Faction':
                    enemy_data['faction'] = value
                elif key == 'Damage':
                    enemy_data['damage_types'] = [x.strip() for x in value.split(',')]

        return enemy_data
    except Exception as e:
        st.warning(f"Error extracting data for '{enemy_name}': {e}")
        return {}

def fetch_enemy_names():
    try:
        data = fetch_wiki_data('query', list='categorymembers', cmtitle='Category:Enemies', cmlimit=500)
        return [enemy['title'] for enemy in data['query']['categorymembers']]
    except Exception as e:
        st.error(f"Error fetching enemy names: {e}")
        return []

def parse_percentage(value: str) -> float:
    try:
        return float(value.strip('%').replace(',', '')) / 100
    except ValueError:
        return 0.0

# Calculation Functions
def calculate_damage(warframe: Warframe, weapon: Weapon, mods: List[Mod], rank: int, enemy: Enemy, enemy_level: int) -> float:
    base_damage = weapon.base_damage
    crit_chance = weapon.base_crit_chance
    crit_mult = weapon.base_crit_mult
    status_chance = weapon.base_status_chance

    for mod in mods:
        mod_stats = mod.get_ranked_stats(rank)
        if 'damage' in mod_stats:
            base_damage *= (1 + mod_stats['damage'])
        if 'critical_chance' in mod_stats:
            crit_chance += mod_stats['critical_chance']
        if 'critical_damage' in mod_stats:
            crit_mult += mod_stats['critical_damage']
        if 'status_chance' in mod_stats:
            status_chance += mod_stats['status_chance']

    avg_crit_mult = 1 + (crit_chance * (crit_mult - 1))
    dps = base_damage * avg_crit_mult * weapon.base_fire_rate

    enemy_stats = enemy.scale_stats(enemy_level)
    damage_reduction = 1 - (enemy_stats['armor'] / (enemy_stats['armor'] + 300))
    effective_dps = dps * damage_reduction

    return effective_dps

def calculate_advanced_survivability(warframe: Warframe, mods: List[Mod], rank: int) -> float:
    health = warframe.base_health
    shield = warframe.base_shield
    armor = warframe.base_armor

    for mod in mods:
        mod_stats = mod.get_ranked_stats(rank)
        if 'health' in mod_stats:
            health *= (1 + mod_stats['health'])
        if 'shield' in mod_stats:
            shield *= (1 + mod_stats['shield'])
        if 'armor' in mod_stats:
            armor *= (1 + mod_stats['armor'])

    effective_health = health * (1 + armor / 300)
    survivability = effective_health + shield
    return survivability

# Database Functions
def init_db():
    Base.metadata.create_all(engine)

def get_all_enemies():
    session = Session()
    try:
        enemies = session.query(EnemyModel).all()
        return [Enemy(
            name=enemy.name,
            faction=enemy.faction,
            base_level=enemy.base_level,
            base_health=enemy.base_health,
            base_armor=enemy.base_armor,
            base_shield=enemy.base_shield,
            damage_types=enemy.damage_types
        ) for enemy in enemies]
    finally:
        session.close()

def add_enemy(enemy: Enemy):
    session = Session()
    try:
        enemy_model = EnemyModel(
            name=enemy.name,
            faction=enemy.faction,
            base_level=enemy.base_level,
            base_health=enemy.base_health,
            base_armor=enemy.base_armor,
            base_shield=enemy.base_shield,
            damage_types=enemy.damage_types
        )
        session.add(enemy_model)
        session.commit()
    except SQLAlchemyError as e:
        session.rollback()
        st.error(f"Error adding enemy to database: {e}")
    finally:
        session.close()

# Streamlit App
def main():
    st.title("Warframe Build Optimizer")

    # Initialize database
    init_db()

    # Check if enemies are in the database, if not, fetch and add them
    session = Session()
    enemy_count = session.query(EnemyModel).count()
    session.close()

    if enemy_count == 0:
        st.info("Fetching enemy data from the Warframe Wiki. This may take a few moments...")
        enemy_names = fetch_enemy_names()
        for enemy_name in enemy_names:
            enemy_data = extract_enemy_data(enemy_name)
            if enemy_data:
                enemy = Enemy(**enemy_data)
                add_enemy(enemy)
        st.success("Enemy data has been added to the database.")

    # Sidebar for user inputs
    st.sidebar.header("Build Configuration")

    # Warframe selection
    warframe_name = st.sidebar.selectbox("Select Warframe", ["Excalibur", "Volt", "Mag"])  # Add more warframes
    warframe = Warframe(warframe_name, **extract_warframe_data(warframe_name))

    # Weapon selection
    weapon_name = st.sidebar.selectbox("Select Weapon", ["Braton", "Lex", "Skana"])  # Add more weapons
    weapon = Weapon(weapon_name, **extract_weapon_data(weapon_name))

    # Mod selection
    available_mods = ["Serration", "Split Chamber", "Vital Sense"]  # Add more mods
    selected_mods = st.sidebar.multiselect("Select Mods", available_mods)
    mods = [Mod(mod_name, **extract_mod_data(mod_name)) for mod_name in selected_mods]

    # Enemy selection
    enemies = get_all_enemies()
    enemy_name = st.sidebar.selectbox("Select Enemy", [enemy.name for enemy in enemies])
    enemy = next((e for e in enemies if e.name == enemy_name), None)

    # Enemy level
    enemy_level = st.sidebar.slider("Enemy Level", 1, 200, 30)

    # Mod rank
    mod_rank = st.sidebar.slider("Mod Rank", 0, 10, 5)

    # Calculate and display results
    if st.button("Calculate"):
        with st.spinner("Calculating..."):
            damage = calculate_damage(warframe, weapon, mods, mod_rank, enemy, enemy_level)
            survivability = calculate_advanced_survivability(warframe, mods, mod_rank)

        st.subheader("Results")
        st.write(f"Effective DPS: {damage:.2f}")
        st.write(f"Survivability: {survivability:.2f}")

        # Visualization
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

        # DPS chart
        ax1.bar(["DPS"], [damage])
        ax1.set_title("Effective DPS")
        ax1.set_ylabel("Damage per Second")

        # Survivability chart
        ax2.bar(["Survivability"], [survivability])
        ax2.set_title("Survivability")
        ax2.set_ylabel("Effective Health")

        st.pyplot(fig)

    # Display build details
    st.subheader("Build Details")
    st.write(f"Warframe: {warframe.name}")
    st.write(f"Weapon: {weapon.name}")
    st.write("Mods:")
    for mod in mods:
        st.write(f"- {mod.name}")

if __name__ == "__main__":
    main()
