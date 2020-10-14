from datetime import datetime
import pandas as pd
import numpy as np
import re
import os 
import ast
from collections import Counter

#set current working directory to where this file is saved
thisdir = os.path.dirname(os.path.abspath(__file__)) + "\\" 
os.chdir(thisdir)

df = pd.read_csv(r"data/user_ad_content.csv", encoding="utf-8")

#extraction ran overnight, midnight is a reasonable simplification
data_gathered = pd.to_datetime('10/12/2020 00:00') 

#format='%M %d, %Y', errors='coerce'
df['joined_dt'] = pd.to_datetime(df['Joined'], infer_datetime_format=True) 
df['days_since_joined'] = data_gathered - df['joined_dt']

#Self descriptors are saved in list form as raw characters,
#must evaluate literally as python list with ast.literal_eval.
df['self_descriptors_literal'] = df['self_descriptors'].apply(lambda x: ast.literal_eval(x))

#Save all values to a single list, then count individual values
full_list = [y for x in list(df['self_descriptors_literal'].values) for y in x]
counts = Counter(full_list)

df_extract = df.copy()

# Get height in inches from highly standardized values 
df_extract['height'] = df_extract['self_descriptors'].str.extract(r'(\d ft \d\d? in)')
def height_to_inches(x):
    if pd.isnull(x):
        return 0
    nums = re.findall(r"(\d+)",x) #all sequences of digits
    ft_to_inches = int(nums[0])*12
    if len(nums) > 1:
        ft_to_inches += int(nums[1])
    return ft_to_inches

df_extract['height_inches'] = df_extract['height'].apply(height_to_inches)

# Extract age as well, highly standardized
df_extract['age'] = df_extract['self_descriptors'].str.extract(r' (\d\d),')

# Here are extracted values as specified from the counts above, 
# From what I can tell, users may list more than one of the multiselect list,
# but they will only select one value from the other lists. 
# Therefore I will create columns for each multiselect value, 
# then separate columns for the other lists 
# with insertions conditional on matching a value.
multiselect_list = ['Incall', "Outcall", "Couple", "BDSM", "FBSM"]
physical_list = ['Athletic', 'BBW', 'Curvy', 'Petite', 'Toned']
race_list = ['Asian', 'Black', 'East Indian', 'Hispanic', 'Latina', 'Middle Eastern', 'Mixed', 'Native American', 'White']
gender_list = ['Female', 'Male', 'TransSexual']

# Create new columns for each item in the multiselect list if it exists
for item in multiselect_list:
    df_extract[item] = df_extract['self_descriptors'].apply(lambda x: 1 if item in x else 0)

# Meta lists
single_assigns = [physical_list, race_list, gender_list]
single_assign_names = ["physical", "race", "gender"]

# For each list given above create a new column,
# and fill that column only when a given option is found
for i in range(len(single_assign_names)):
    
    #get current list and column name
    current_list = single_assigns[i]
    current_column = single_assign_names[i]
    
    #create the column with empty strings
    df_extract[current_column] = ""

    #check if each item in this list is found
    for item in current_list:
        
        def assign_item_else_nothing(x):
            """Function to only update to value if exists, otherwise
            give existing value."""
            #as a row, column names are not attached, 
            #must find column numbers
            dfcols = list(df_extract.columns)
            col_self_desc = int(dfcols.index('self_descriptors'))
            col_phys = int(dfcols.index(current_column))
            self_desc_val = x[col_self_desc]

            internal_item = item

            if str(internal_item).lower() in self_desc_val.lower():
                return str(internal_item)
            else:
                return x[col_phys]
            
        # apply given function on every row of the database
        df_extract[current_column] = df_extract.apply(assign_item_else_nothing, axis = 1)

df_donation = df_extract.copy()
#list(df_desc['donation_options'].values)
#Self descriptors are saved in list form as raw characters,
#must evaluate literally as python list with ast.literal_eval.
def liteval_if_list(x):
    x = str(x)
    if ']' in x and '[' in x:
        return ast.literal_eval(x)
    else:
        return [[x]]

df_donation['donation_lists'] = df_donation['donation_options'].apply(liteval_if_list)

df_donation_only = df_donation[['url','username','donation_lists']].explode('donation_lists')
df_donation_only = df_donation_only.dropna()

def multiplyers(item, xsearch):
    xsearch = [x.replace("@", ".") for x in xsearch[0]]
    fullmatch = 'x'.join(xsearch)
    outnum = int(xsearch[0]) * int(xsearch[1])
    return [fullmatch, outnum]

def clean_donations(x):
    outlist = []
#     if "deposit" in ''.join(x).lower() or "call me" in ''.join(x).lower():
#         return None
    
    for item in x:
        item = re.sub("(\d{3}[\-\/\)]?\d{3}[\-\/\)]?\d{4})", "", item) #remove phone numbers
        item = re.sub("(per|rate|is) ", " ", item.lower().strip()) #remove per and rate
        item = re.sub(r"\$(\d+\.?\d?)k", r"\g<1>000", item) #convert $1k to 1000
        item = re.sub(r"(\d)\,(\d\d\d)", r"\g<1>\g<2>", item) #convert 1,000 to 1000
        item = re.sub(r"(\d+)\-(\d+)", r" \g<1> ", item) #convert 1,000 to 1000
        item = item.replace(".00", "").replace(r"1/2", "0.5").replace(".","@") #remove post-number decimals
        
        item = re.sub(r"([:* \/\~\(]|\@\@)", " ", item) #convert unusual/multiple spacers to a space
        item = re.sub(r"[^a-z0-9 \,\/\-\@]", "", item) # remove unexpected characters
        
        #convert 100x2 to 200 etc. 
        xsearch = re.findall(r"([\d\@]+)x([\d\@]+)", item)
        if xsearch:
            xsearch = multiplyers(item, list(xsearch))
            item = item.replace(xsearch[0], str(xsearch[1]))
        
        #item = re.sub(r"(full)", " 1 ", item) #convert full to 1, i.e. full hour = 1 hour
        
        item = re.sub(r"(qk|quick)", " 0@25 hr ", item) #convert jargon qk to 15 min
        item = re.sub(r"(hhr|hh|half hour|half hr)", " 0@5 hr ", item) #convert "half hour" jargon to 0.5 hours
        item = re.sub(r"(half)", " 0@5 ", item) #convert remaining "half" to 0.5
        item = re.sub(r"(h[ours\.\@]+? |hours?)", " hr ", item) #make hour text consistent
        item = re.sub(r"(\d{3,})[\s|\/]+hr", " \g<1> 1 hr ", item) #dollars per hour to dollars per 1 hour
        item = re.sub(r"(min|qk)", " \g<1> ", item) #make hour text consistent
        item = re.sub(r"([a-z]+)([\d\@]+)([a-z]+)", r" \g<1> \g<2> \g<3> ", item) #add space around numbers in text
        item = re.sub(r"\/?([\d\@]+)[ \/\@\-]*(h[a-z]*|inout|qk|min[a-z]*)\/?", r" \g<2> \g<1> ", item) #rearrange number-text to text number
        item = re.sub(r"\s{2,}", " ", item).strip().lstrip(",") # simplify spaces and strip
        item = re.split(r"([a-zA-Z]+|[\d\@]+)[ \-\/\,]+([\d\@]+|hr|qk|min[a-z]*)", item)
        
        #ensure lists are joined and items appended
        if type(item) == list:
            outlist += item
        else:
            outlist.append(item)
    outlist = [re.sub(r"[\/\-]", "", x.strip().rstrip("s")).replace("@",".") for x in outlist]
    outlist = [x for x in outlist if x]
    return outlist
    
# (?:mins?|hours?|gfe|days?|week) $?\d+
df_donation_only['donation_list2'] = df_donation_only['donation_lists'].apply(clean_donations)

bool_cols = ["incall", "outcall", "fly", "gfe", "greek"]
# Create new columns for each item in the multiselect list if it exists
for item in bool_cols:
    df_donation_only[item] = df_donation_only['donation_lists'].apply(lambda x: 1 if item in ''.join(x).lower() else 0)

bool_cols = ["min", "hr", "qk", "day", "overnight", "week"]
# Create new columns for each item in the multiselect list if it exists
for item in bool_cols:
    df_donation_only[item] = df_donation_only['donation_list2'].apply(lambda x: 1 if item in x else 0)

def num_only_list(x):
    numlist = []
    for item in x:
        numbers = re.findall(r'(\d+\.\d+|\d+)', item)
        if numbers:
            numlist += numbers
            
#     # if it's a phone number, exit
#     if sum([len(a) for a in numlist]) == 10 and len(numlist) == 3:
#         return []
    
    numlist = [float(n) for n in numlist if float(n) > 0]
    
    # if empty list, or the max value is too low to have $, exit
    if not numlist or max(numlist) < 15:
        return []
    if len(numlist) % 2 != 0:
        numlist.append(1.0)
    
    numlist = sorted(numlist)
    return numlist
    
df_donation_only['num_only_list'] = df_donation_only['donation_list2'].apply(num_only_list)

def split_list(x):
    if type(x) != list or not x or len(x) %2 > 0:
        return None, None
    length = len(x)
    mid = int(length / 2)
    return x[:mid], x[mid:]

splitup = df_donation_only['num_only_list'].apply(split_list)

split_df = pd.DataFrame(splitup, columns=["quantities", "costs"])
 #df_donation_only[["quantities", "costs"]]
#full_list = [y for x in df_donation_only['donation_list2'].values for y in x]
#set(full_list)
startval = 1
rangevals = list(range(startval,startval+59))
df_donation_only.iloc[rangevals]
