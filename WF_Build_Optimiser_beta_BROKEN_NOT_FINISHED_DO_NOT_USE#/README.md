### README.md

# Warframe Build Optimizer

## Overview
The Warframe Build Optimizer is a Python-based application that leverages Streamlit, SQLAlchemy, and various APIs to collect and analyze Warframe data. Users can select their Warframe, weapon, and mods, and then optimize their builds based on specific objectives (damage output or survivability) against particular enemies.

## Features
- Fetch data from Warframe APIs to populate a local SQLite database.
- Analyze and optimize Warframe builds based on selected mods and weapons.
- Visualize performance metrics for builds.
- User-friendly interface powered by Streamlit.

## Technologies
- **Python**: The programming language used for backend logic.
- **Streamlit**: For creating a web application interface.
- **SQLAlchemy**: For ORM and managing SQLite database.
- **BeautifulSoup**: For parsing HTML content from the Warframe Wiki.
- **Requests**: For making HTTP requests.

## Installation
1. Clone the repository.
2. Make sure you have Python installed. It's recommended to use Python 3.7 or higher.
3. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the application:
   ```bash
   streamlit run app.py
   ```

## Usage
- Upon launching the app, select your desired Warframe and weapon from the dropdown menus.
- Choose mods from the provided multiselect.
- Set the ranks for them using the slider.
- Input the target enemy's armor and shield, then select your optimization goal (Damage or Survivability).
- Click "Optimize" to view the results.

## Data Sources
The application fetches data from:
- **Warframe Wiki API**: Provides detailed information on warframes, weapons, and enemy stats.
- **Snekw API**: Used to get lists of warframes, weapons, and mods.

## Database Structure
The SQLite database consists of the following tables:
- **warframes**: Stores information about each Warframe.
- **weapons**: Stores stats for each weapon.
- **mods**: Contains details on available mods.

## Contributions
Feel free to submit issues or pull requests. Any contributions are welcome!

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.

## Acknowledgments
- Warframe community for providing data through the wiki.
- Streamlit developers for their easy-to-use framework.
