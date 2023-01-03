import re
from time import sleep
from urllib.request import urlopen
from bs4 import BeautifulSoup




def getUnitList():
    check_list = []

    mythicUnitList = "https://animeadventures.fandom.com/wiki/Category:Mythic_Units"
    secretUnitList = "https://animeadventures.fandom.com/wiki/Category:Secret_Units"

    
    check_list.append(mythicUnitList)
    check_list.append(secretUnitList)
    units = []
    for li in check_list:
        page = urlopen(li)
        html = page.read().decode("utf-8")
        mythicSoup = BeautifulSoup(html, "html.parser")
        links = mythicSoup.find_all(class_= "category-page__member-link")
        
        for l in links:
            title = l.string
            link = l["href"]
            if (title != 'User:Babamo/Sandbox'):
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

    exportDict = {"Name":unit.get("name")}

    
    #Remove all HTML tags for easier filtering
    text = soup.getText()


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
    has_spawns = False
    if len(spawn_level_one) != 0:
        has_spawns = True

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
        spawn_level_one = spawn_level_one
        spawn = spawn_level_one_hundred



    for i in range(len(total_cost)):
        upgrade_split_index = total_cost[i].find("-")
        damage_split_index = damage_level_one[i].find(":")
        range_split_index = attack_range_level_one[i].find(":")
        spa_split_index = spa_level_one[i].find(":")
        dps_split_index = dps_level_one[i].find(":")
        if has_spawns:
            spawn_split_index = spawn_level_one[i].find(":")
            
        
        #Setting all the key names
        #upgr_key can be either "Deployment" or "Upgrade x"
        dict_upgr_key = total_cost[i][0:(upgrade_split_index-1)]
        dict_dmg_key = "Damage"
        dict_rng_key = "Range"
        dict_spa_key = "SPA"
        dict_dps_key = "DPS"
        dict_spawn_key = "Spawn"



        #adding new dictionary to stat list. 
        level_one_stats.append({})

        #Setting all the key values for level one
        dict_upgr_val = total_cost[i][(upgrade_split_index+2):(len(total_cost[i])-1)] #len-1 to chop off the Yen symbol
        dict_dmg_val = damage_level_one[i][(damage_split_index+2):len(damage_level_one[i])]
        dict_rng_val = attack_range_level_one[i][(range_split_index+2):len(attack_range_level_one[i])]
        dict_spa_val = spa_level_one[i][(spa_split_index+2):len(spa_level_one[i])]
        dict_dps_val = dps_level_one[i][(dps_split_index+2):len(dps_level_one[i])]
        if has_spawns:
            dict_spawn_val = spawn_level_one[i][(spawn_split_index+2):(len(spawn_level_one[i])-3)] #len-3 to chop off " HP"

        #Putting keys and values into newly added dict
        level_one_stats[i][dict_upgr_key] = dict_upgr_val
        level_one_stats[i][dict_dmg_key] = dict_dmg_val
        level_one_stats[i][dict_rng_key] = dict_rng_val
        level_one_stats[i][dict_spa_key] = dict_spa_val
        level_one_stats[i][dict_dps_key] = dict_dps_val
        if has_spawns:
            level_one_stats[i][dict_spawn_key] = dict_spawn_val

        #now to add level 100 dict to the lsit
        level_one_hundred_stats.append({})

        #Setting all the key values for level one hundreed
        dict_upgr_val = total_cost[i][(upgrade_split_index+2):(len(total_cost[i])-1)] #len-1 to chop off the Yen symbol
        dict_dmg_val = damage_level_one_hundred[i][(damage_split_index+2):len(damage_level_one_hundred[i])]
        dict_rng_val = attack_range_level_one_hundred[i][(range_split_index+2):len(attack_range_level_one_hundred[i])]
        dict_spa_val = spa_level_one_hundred[i][(spa_split_index+2):len(spa_level_one_hundred[i])]
        dict_dps_val = dps_level_one_hundred[i][(dps_split_index+2):len(dps_level_one_hundred[i])]
        if has_spawns:
            dict_spawn_val = spawn_level_one_hundred[i][(spawn_split_index+2):(len(spawn_level_one_hundred[i])-3)] #len-3 to chop off " HP"

        #Putting keys and values into newly added dict
        level_one_hundred_stats[i][dict_upgr_key] = dict_upgr_val
        level_one_hundred_stats[i][dict_dmg_key] = dict_dmg_val
        level_one_hundred_stats[i][dict_rng_key] = dict_rng_val
        level_one_hundred_stats[i][dict_spa_key] = dict_spa_val
        level_one_hundred_stats[i][dict_dps_key] = dict_dps_val
        if has_spawns:
            level_one_hundred_stats[i][dict_spawn_key] = dict_spawn_val

    exportDict["Level 1 Stats"] = level_one_stats
    exportDict["Level 100 Stats"] = level_one_hundred_stats

    
    return exportDict


units = getUnitList()

#/*count = 1
#for pair in units:
#    print("{}: {}".format(count,pair))
#    count+=1

unit_stats_master = []

count = 0
for pair in units:
    unit_stats_master.append(getUnitBaseStats(pair))
    print("{}: Finished Getting {} Stats".format(count,unit_stats_master[count].get("Name")))
    count+=1

for u in unit_stats_master:
    print("{}\nLevel 1 Stats\n{}\nLevel 100 Stats\n{}\n\n".format(u.get("Name"), u.get("Level 1 Stats"), u.get("Level 1 Stats")))
    #print("\'{}\'s deployment cost is {}\n\n".format(u.get("Name"), u.get("Level 1 Stats")[0].get("Deployment")))