
"""
# coding: utf-8

Talks markdown generator for academicpages
Takes a TSV of talks with metadata and converts them for use with 
academicpages.github.io. This is an interactive Jupyter notebook 
The core python code is also in `talks.py`. 
Run either from the `markdown_generator` folder after replacing `talks.tsv` 
with one containing your data.
"""


import pandas as pd
import os
import shutil

import glob
import getorg
from geopy import Nominatim
from geopy.exc import GeocoderTimedOut
import yaml


def html_escape(text):
    if type(text) is str:
        return "".join(html_escape_table.get(c,c) for c in text)
    else:
        return "False"

def process_talks():
    """
     ## Data format
    The TSV needs to have the following columns: title, type, url_slug, 
    venue, date, location, talk_url, description, with a header at the top. 
    Many of these fields can be blank, but the columns must be in the TSV.
    
    - Fields that cannot be blank: `title`, `url_slug`, `date`. All else 
      can be blank. `type` defaults to "Talk" 
    - `date` must be formatted as YYYY-MM-DD.
    - `url_slug` will be the descriptive part of the .md file and the 
       permalink URL for the page about the paper. 
        - The .md file will be `YYYY-MM-DD-[url_slug].md` and the permalink 
          will be `https://[yourdomain]/talks/YYYY-MM-DD-[url_slug]`
        - The combination of `url_slug` and `date` must be unique, as it 
          will be the basis for your filenames
    """

    """
    # ## Import TSV
    Pandas makes this easy with the read_csv function. We are using a 
    SV, so we specify the separator as a tab, or `\t`.
    I found it important to put this data in a tab-separated values format, 
    because there are a lot of commas in this kind of data and comma-separated 
    values can get messed up. However, you can modify the import statement, 
    as pandas also has read_excel(), read_json(), and others.
    """
    talks = pd.read_csv("talks.csv", sep=",", header=0, encoding='utf-8')
    print(talks.head())


    """
    # ## Escape special characters
    # YAML is very picky about how it takes a valid string, so we are 
    replacing single and double quotes (and ampersands) with their HTML 
    encoded equivilents. This makes them look not so readable in raw format, 
    but they are parsed and rendered nicely.
    """
    html_escape_table = {
        "&": "&amp;",
        '"': "&quot;",
        "'": "&apos;"
        }


    # ## Creating the markdown files
    """# This is where the heavy lifting is done. This loops through all 
    the rows in the TSV dataframe, then starts to concatentate a big string 
    (```md```) that contains the markdown for each type. It does the YAML 
    metadata first, then does the description for the individual page."""

    loc_dict = {}

    for row, item in talks.iterrows():
        md_filename = str(item.date) + "-" + item.url_slug + ".md"
        html_filename = str(item.date) + "-" + item.url_slug 
        # year = item.date[:4]
        year = item.date
        
        md = "---\ntitle: \""   + item.title + '"\n'
        md += "collection: talks" + "\n"
        
        if len(str(item.type)) > 3:
            md += 'type: "' + item.type + '"\n'
        else:
            md += 'type: "Talk"\n'
        
        md += "permalink: /talks/" + html_filename + "\n"
        
        if len(str(item.venue)) > 3:
            md += 'venue: "' + item.venue + '"\n'
            
        if len(str(item.date)) > 3:
            md += "date: " + str(item.date) + "\n"
        
        if len(str(item.location)) > 3:
            md += 'location: "' + str(item.location) + '"\n'
               
        md += "---\n"
        
        
        if len(str(item.talk_url)) > 3:
            md += "\n[More information here](" + item.talk_url + ")\n" 
            
        
        if len(str(item.description)) > 3:
            md += "\n" + html_escape(item.description) + "\n"
            
            
        md_filename = os.path.basename(md_filename)
        
        talkdir = os.path.join(os.getcwd(), "temp-talks")
        if not os.path.exists(talkdir):
            os.makedirs(talkdir)
        with open(os.path.join(talkdir, md_filename), "w") as f:
            f.write(md)


# These files are in the `temp-talks` directory
def make_talk_map():

    # Set the default timeout, in seconds
    TIMEOUT = 5

    # Collect the Markdown files
    talk_path = os.path.join(os.getcwd(), "temp-talks", "*.md")
    g = glob.glob(talk_path)

    # Prepare to geolocate
    geocoder = Nominatim(user_agent="academicpages.github.io")
    location_dict = {}
    location = ""
    permalink = ""
    title = ""

    # Perform geolocation
    for file in g:
        # Read the file
        with open(file, 'r') as f:
            content = f.read()
        parts = content.split('---', 2)

        if len(parts) > 1:
            yaml_header_string = parts[1].strip()
            # Parse the YAML string into a dictionary
            data = yaml.safe_load(yaml_header_string)

        # Press on if the location is not present
        if 'location' not in data:
            continue

        # Prepare the description
        title = data['title'].strip()
        venue = data['venue'].strip()
        location = data['location'].strip()
        description = f"{title}<br />{venue}; {location}"
        
        # Geocode the location and report the status
        try:
            location_dict[description] = geocoder.geocode(location, timeout=TIMEOUT)
            print(description, location_dict[description])
        except ValueError as ex:
            print(f"Error: geocode failed on input {location} with message {ex}")
        except GeocoderTimedOut as ex:
            print(f"Error: geocode timed out on input {location} with message {ex}")
        except Exception as ex:
            print(f"An unhandled exception occurred while processing input {location} with message {ex}")

    # Save the map
    talkmap_dir = os.path.join(os.getcwd(), "..", "talkmap")
    m = getorg.orgmap.create_map_obj()
    getorg.orgmap.output_html_cluster_map(location_dict, folder_name=talkmap_dir, hashed_usernames=False)

    shutil.rmtree(os.path.join(os.getcwd(), "temp-talks"))
    print("\nAfter making map, need to manually change lat/long to [35, -96],\n"
        "and zoom to 3. Also need to comment out the 'Mouse over ...'\n"
        "This is done in talkmap/map.html")

process_talks()
make_talk_map()