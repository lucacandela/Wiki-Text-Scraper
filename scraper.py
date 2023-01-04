import re
from time import sleep
from urllib.request import urlopen
from bs4 import BeautifulSoup
import json
from datetime import datetime
from pathlib import Path
import os

def getUnitList():
    check_list = []

    mythicUnitList = "https://animeadventures.fandom.com/wiki/Category:Mythic_Units"
    secretUnitList = "https://animeadventures.fandom.com/wiki/Category:Secret_Units"
    legendary_unit_list = "https://animeadventures.fandom.com/wiki/Category:Legendary_Units"
    epic_unit_list = "https://animeadventures.fandom.com/wiki/Category:Epic_Units"
    rare_unit_list = "https://animeadventures.fandom.com/wiki/Category:Rare_Units"


    
    check_list.append(mythicUnitList)
    check_list.append(secretUnitList)
    check_list.append(legendary_unit_list)
    check_list.append(epic_unit_list)
    check_list.append(rare_unit_list)
    units = []
    for li in check_list:
        page = urlopen(li)
        html = page.read().decode("utf-8")
        mythicSoup = BeautifulSoup(html, "html.parser")
        links = mythicSoup.find_all(class_= "category-page__member-link")
        
        for l in links:
            title = l.string
            link = l["href"]
            if (title[0:5] != 'User:'):
                units.append({"name":title,"link":("https://animeadventures.fandom.com"+link)})

    return units
    

def getUnitBaseStats(unit: dict):

    url = unit.get("link","No link in dict")
    page = urlopen(url)
    html = page.read().decode("utf-8")
    soup = BeautifulSoup(html, "html.parser")

    # Get rid of all the extra stats on the html page that calculate orwin buff, kisoko buff, and sakura buff
    # https://stackoverflow.com/questions/32063985/deleting-a-div-with-a-particular-class-using-beautifulsoup
    for s in soup.find_all("span", {'class':'mw-collapsed'}): 
        s.decompose()

    #Find all category tags
    categoryTags = []
    for s in soup.find_all("a", {'class':'newcategory'}):
        if s !=None:
            categoryTags.append(s.text)
    categoryTags = list(set(categoryTags))

    #Add name
    exportDict = {"Name":unit.get("name")}
    exportDict["Tags"] = categoryTags
    
    #Remove all HTML tags for easier filtering
    text = soup.getText()
    #print(text)

    #Add spawn_cap
    spawn_cap = re.findall("Spawn Cap\n.*?\\n\\n\\n",text, re.IGNORECASE)
    if len(spawn_cap) > 0:
        spawn_cap[0] = spawn_cap[0].replace("\n"," ")
        spawn_cap = re.findall("[\\d]+",spawn_cap[0],re.IGNORECASE)
        exportDict["Placement Count"] = spawn_cap[0]
    else:
        exportDict["Placement Count"] = "Incomplete Wiki Data"
    
    #Add tower type:
    tower_type = re.findall("Tower Type\\n.*?\\n\\n\\n",text,re.IGNORECASE)
    tower_type[0] = tower_type[0].replace("\n"," ")
    tower_type = re.findall("[A-Z]+.*?",tower_type[0],re.IGNORECASE)
    tower_type.remove("Tower")
    tower_type.remove("Type")
    exportDict["Tower Type"] = tower_type
    
    #Add damage types:
    damage_type = re.findall("Damage Type\n.*?\n\n\n",text,re.IGNORECASE)
    if len(damage_type) > 0:
        damage_type[0] = damage_type[0].replace("\n", " ")
        damage_type = re.findall("[A-Za-z]+.*?",damage_type[0],re.IGNORECASE)
        damage_type.remove("Damage")
        damage_type.remove("Type")
        exportDict["Damage Type"] = damage_type
    else:
        exportDict["Damage Type"] = "None"

    second_damage_type = re.findall("Secondary Damage Type\n.*?\n\n\n", text, re.IGNORECASE)
    #not all units have a secondary damage typing
    if len(second_damage_type) != 0:
        second_damage_type[0] = second_damage_type[0].replace("\n"," ")
        second_damage_type = re.findall("[A-Za-z]+.*?",second_damage_type[0],re.IGNORECASE)
        second_damage_type.remove("Secondary")
        second_damage_type.remove("Damage")
        second_damage_type.remove("Type")
        exportDict["Secondary Damage Type"] = second_damage_type

    #Add attack AOEs
    #Types Single = SINGLE, AOE (CIRCLE) = RADIUS, AOE (CONE) = ANGLE, AOE(FULL) = FULL, AOE (LINE) = WIDTH
    aoe_type = re.findall("((Deployment.*?\n)|(Upgrade \d.*?\n)|(Attack Type Change to))"
                            +".*?"
                            +"((None)|(Single)|(AoE \(Circle\).*?\\b\d[\d,.]*)|(AoE \(Full\))|(AoE \(Line\).*?\\b\d[\d,.]*)|(AoE \(Cone\).*?\\b\d[\d,.]*))",
                            text,re.IGNORECASE)
    #remove duplicates for lv 1 and lv 100
    aoe = set(aoe_type[::2])
    aoe_type = []
    for a in aoe:
        aoe_type.append(a)
    aoe_list = []
    for a in aoe_type:
        aoe_list.append((set(a)))
    aoe_type = []
    for a in aoe_list:
        a.remove("")
        a = sorted(a)
        a.reverse()
        loop_list = []
        for b in a:
            loop_list.append(b.replace("\n",""))
        loop_list = sorted(loop_list)
        loop_list.reverse()
        aoe_type.append(loop_list)
    #Sort lists so that Upgrade or Deployment comes first
    aoe_type = sorted(aoe_type)
    for a in aoe_type:
        if a[0] == "None" or a[0] == "Single":
            a.reverse()
    #remove the extraneous parts
    aoe_list = []
    for item in aoe_type:
        match = re.findall("(Upgrade \d)|(Deployment)", item[0], re.IGNORECASE)
        loop_list = []
        for m in match:
            for l in m:
                loop_list.append(l)
        loop_list.remove("")
        item[0] = loop_list[0]
        aoe_list.append({item[0]:item[1]})
    exportDict["Attack Type"] = aoe_list



    total_cost = []
    
    #Costs can either start with "Deployment - " or "Upgrade x -" so I need two statements to catch them both
    #Could be one statement if I knew regex better
    deploy_cost = re.findall("deployment.*?\\b\d[\d,.]*\\b¥", text, re.IGNORECASE)
    total_cost.append(deploy_cost[0])

    upgrade_cost = re.findall("Upgrade \d.*?\\b\d[\d,.]*\\b¥", text, re.IGNORECASE)
    upgrade_cost = upgrade_cost[::2]

    #Final step to add all the costs together
    for i in upgrade_cost:
        total_cost.append(i)

    # \\b\d[\d,.]*\\b Will catch all numbers with commas and decimals
    damage = re.findall("Damage\\: \\b\d[\d,.]*\\b", text, re.IGNORECASE)
    damage_level_one = damage[::2]
    damage_level_one_hundred = damage[1::2]

    attack_range = re.findall("Range\\: \\b\d[\d,.]*", text, re.IGNORECASE)
    attack_range_level_one = attack_range[::2]
    attack_range_level_one_hundred = attack_range[1::2]

    spa = re.findall("SPA\\: \\b\d[\d,.]*", text, re.IGNORECASE)
    spa_level_one = spa[::2]
    spa_level_one_hundred = spa[1::2]

    dps = re.findall("DPS\\: \\b\d[\d,.]*", text, re.IGNORECASE)
    dps_level_one = dps[::2]
    dps_level_one_hundred = dps[1::2]

    farm_income = re.findall("\\b\d[\d,.]*¥ per wave", text, re.IGNORECASE)
    farm_income_level_one = farm_income[::2]
    farm_income_level_one_hundred = farm_income[1::2]

    spawn = re.findall("Spawn\\: \\b\d[\d,.]*\\b HP", text, re.IGNORECASE)
    spawn_level_one = spawn[::2]
    spawn_level_one_hundred = spawn[1::2]


    level_one_stats = []
    level_one_hundred_stats = []

    #error checking. Not all units have all of these stats
    damage_list = []
    attack_range_list = []
    spa_list = []
    dps_list = []
    spawn_list = []
    farm_list = []
    has_farms = False
    has_spawns = False
    if len(spawn_level_one) != 0:
        has_spawns = True
    if len(farm_income_level_one) != 0:
        has_farms = True

    if len(damage_level_one) < len(total_cost):
        for x in range(len(total_cost)):
            damage_list.append("Damage: Incomplete Wiki Data")
        damage_level_one = damage_list
        damage_level_one_hundred = damage_list
    
    if len(attack_range_level_one) < len(total_cost):
        for x in range(len(total_cost)):
            attack_range_list.append("Range: Incomplete Wiki Data")
        attack_range_level_one = attack_range_list
        attack_range_level_one_hundred = attack_range_list

    if len(spa_level_one) < len(total_cost):
        for x in range(len(total_cost)):
            spa_list.append("SPA: Incomplete Wiki Data")
        spa_level_one = spa_list
        spa_level_one_hundred = spa_list

    if len(dps_level_one) < len(total_cost):
        for x in range(len(total_cost)):
            dps_list.append("DPS: Incomplete Wiki Data")
        dps_level_one = dps_list
        dps_level_one_hundred = dps_list

    if (len(spawn_level_one) < len(total_cost)) and (has_spawns):
        for x in range(len(total_cost)):
            spawn_list.append("Spawn: Incomplete Wiki Data")
        spawn_level_one = spawn_list
        spawn_level_one_hundred = spawn_list
    if (len(farm_income_level_one)< len(total_cost)) and has_farms:
        for x in range(len(total_cost)):
            farm_list.append("N/A¥ Incomplete Wiki Data")
        farm_income_level_one = farm_list
        farm_income_level_one_hundred = farm_list



    for i in range(len(total_cost)):
        upgrade_split_index = total_cost[i].find("-")
        damage_split_index = damage_level_one[i].find(":")
        range_split_index = attack_range_level_one[i].find(":")
        spa_split_index = spa_level_one[i].find(":")
        dps_split_index = dps_level_one[i].find(":")
        if has_spawns:
            spawn_split_index = spawn_level_one[i].find(":")
        if has_farms:
            farm_split_index = farm_income_level_one[i].find("¥")
            
        
        #Setting all the key names
        #upgr_key can be either "Deployment" or "Upgrade x"
        dict_upgr_key = total_cost[i][0:(upgrade_split_index-1)]
        dict_dmg_key = "Damage"
        dict_rng_key = "Range"
        dict_spa_key = "SPA"
        dict_dps_key = "DPS"
        dict_spawn_key = "Spawn"
        dict_farm_key = "Income"


        #adding new dictionary to stat list. 
        level_one_stats.append({})

        #Setting all the key values for level one
        dict_upgr_val = total_cost[i][(upgrade_split_index+2):(len(total_cost[i])-1)] #len-1 to chop off the Yen symbol
        if not has_farms:
            dict_dmg_val = damage_level_one[i][(damage_split_index+2):len(damage_level_one[i])]
            dict_rng_val = attack_range_level_one[i][(range_split_index+2):len(attack_range_level_one[i])]
            dict_spa_val = spa_level_one[i][(spa_split_index+2):len(spa_level_one[i])]
            dict_dps_val = dps_level_one[i][(dps_split_index+2):len(dps_level_one[i])]
        else:
            dict_farm_val = farm_income_level_one[i][(0):farm_split_index]
        if has_spawns:
            dict_spawn_val = spawn_level_one[i][(spawn_split_index+2):(len(spawn_level_one[i])-3)] #len-3 to chop off " HP"

        #Putting keys and values into newly added dict
        level_one_stats[i][dict_upgr_key] = dict_upgr_val
        if not has_farms:
            level_one_stats[i][dict_dmg_key] = dict_dmg_val
            level_one_stats[i][dict_rng_key] = dict_rng_val
            level_one_stats[i][dict_spa_key] = dict_spa_val
            level_one_stats[i][dict_dps_key] = dict_dps_val
        else:
            level_one_stats[i][dict_farm_key] = dict_farm_val
        if has_spawns:
            level_one_stats[i][dict_spawn_key] = dict_spawn_val

        #now to add level 100 dict to the lsit
        level_one_hundred_stats.append({})

        #Setting all the key values for level one hundreed
        dict_upgr_val = total_cost[i][(upgrade_split_index+2):(len(total_cost[i])-1)] #len-1 to chop off the Yen symbol
        if not has_farms:
            dict_dmg_val = damage_level_one_hundred[i][(damage_split_index+2):len(damage_level_one_hundred[i])]
            dict_rng_val = attack_range_level_one_hundred[i][(range_split_index+2):len(attack_range_level_one_hundred[i])]
            dict_spa_val = spa_level_one_hundred[i][(spa_split_index+2):len(spa_level_one_hundred[i])]
            dict_dps_val = dps_level_one_hundred[i][(dps_split_index+2):len(dps_level_one_hundred[i])]
        else:
            dict_farm_val = farm_income_level_one_hundred[i][(0):farm_split_index]
        if has_spawns:
            dict_spawn_val = spawn_level_one_hundred[i][(spawn_split_index+2):(len(spawn_level_one_hundred[i])-3)] #len-3 to chop off " HP"

        #Putting keys and values into newly added dict
        level_one_hundred_stats[i][dict_upgr_key] = dict_upgr_val
        if not has_farms:
            level_one_hundred_stats[i][dict_dmg_key] = dict_dmg_val
            level_one_hundred_stats[i][dict_rng_key] = dict_rng_val
            level_one_hundred_stats[i][dict_spa_key] = dict_spa_val
            level_one_hundred_stats[i][dict_dps_key] = dict_dps_val
        else:
            level_one_hundred_stats[i][dict_farm_key] = dict_farm_val
        if has_spawns:
            level_one_hundred_stats[i][dict_spawn_key] = dict_spawn_val
        

    exportDict["Level 1 Stats"] = level_one_stats
    exportDict["Level 100 Stats"] = level_one_hundred_stats

    
    return exportDict


units = getUnitList()

#Test cases
#luci = getUnitBaseStats(units[146])
#bulma = getUnitBaseStats(units[155])
#testUnit = getUnitBaseStats(units[217])
#ice_queen_evo = getUnitBaseStats(units[135])

unit_stats_master = []

now = datetime.now()
current_date = now.strftime("%m_%d_%Y %H.%M.%S")
rel_directory= Path(__file__).parent.absolute()
rel_directory = str(rel_directory)
json_folder = rel_directory+"\\JSON Files\\"+current_date
Path(json_folder).mkdir(parents=True, exist_ok=True)

unit_count = 1
for pair in units:
    u = getUnitBaseStats(pair)
    unit_stats_master.append(u)
    file = open("{}\\Unit {}.json".format(json_folder,unit_count), 'w')
    json.dump(u, file, indent=4, separators=(',', ': '))
    file = open("{}\\Logs.txt".format(json_folder), 'a')
    file.write("{}: Finished Getting {} Stats\n".format(unit_count,unit_stats_master[unit_count-1].get("Name")))
    unit_count+=1
