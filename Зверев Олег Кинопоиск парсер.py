import sys
sys.version_info

# pip install kinopoisk-api-unofficial-client

from kinopoisk_unofficial.kinopoisk_api_client import KinopoiskApiClient
from kinopoisk_unofficial.request.films.film_request import FilmRequest
import time
import pickle
from kinopoisk_unofficial.request.staff.staff_request import StaffRequest
import re
from py2neo import Graph


api_client = KinopoiskApiClient("3234199f-eb6e-4667-ae9f-9a26a19feff0")


responses = {}
i=200
while True:
    # time.sleep(1)
    try :
        request = FilmRequest(i)
        response = api_client.films.send_film_request(request)
        responses[i] = (response.__dict__)
        print("film with id", i, "added")
    except:
        print("No id", i)

    if len(responses) >= 200:
        break
    i+=1
    



with open('films.pickle', 'wb') as handle:
    pickle.dump(responses, handle, protocol=pickle.HIGHEST_PROTOCOL)



film_staff = {}
for film in res.keys():
    request = StaffRequest(film)
    response = api_client.staff.send_staff_request(request)
    film_staff[film] = response



with open('film_staff.pickle', 'wb') as handle:
    pickle.dump(film_staff, handle, protocol=pickle.HIGHEST_PROTOCOL)




with open('films.pickle', 'rb') as handle:
    res = pickle.load(handle)


with open('film_staff.pickle', 'rb') as handle:
    staff = pickle.load(handle)



input_text = ""

new_film_names = {}
for film in res.keys():
    try :
        film_name = re.sub(r"\W+", "", res[film]["film"].__dict__["name_original"].replace(" ", ""))
    except:
        try:
            film_name = re.sub(r"\W+", "", res[film]["film"].__dict__["name_en"].replace(" ", ""))
        except:
            film_name = "m" + str(film)

    try:
        flag = int(film_name[0])
        film_name = "m" + film_name
    except:
        pass
    new_film_names[film] = film_name
    input_text += f'CREATE ({film_name}:Movie '
    input_text += "{"
    tagline = str(res[film]["film"].__dict__["slogan"]).replace("'", "").replace('"', '')
    input_text += f'title:"{res[film]["film"].__dict__["name_ru"]}", released:{res[film]["film"].__dict__["year"]}, tagline:"{tagline}"'
    input_text += "}) "



people_id = []
people_new_name = {}
for film in staff.keys():
    for person in staff[film].__dict__["items"]:
        if person.__dict__["profession_text"] in ["Режиссеры", "Актеры", "Продюсеры", "Сценаристы"] and person.__dict__["staff_id"] not in people_id:
            people_id.append(person.__dict__["staff_id"])

            if person.__dict__["name_en"] == "":
                person_name = "p" + str(person.__dict__["staff_id"])
            else:
                person_name = re.sub(r"\W+", "", person.__dict__["name_en"].replace(" ", ""))
            
            if person_name in people_new_name.values():
                person_name += str(person.__dict__["staff_id"])
            people_new_name[person.__dict__["staff_id"]] = person_name
            input_text += f'CREATE ({person_name}:Person '
            input_text += "{"
            input_text += f'name:"{person.__dict__["name_ru"]}"'
            input_text += "}) "


roles = {"Режиссеры":"DIRECTED", "Продюсеры":"PRODUCED", "Сценаристы":"WROTE"}

for film in staff.keys():
    for person in staff[film].__dict__["items"]:
        if person.__dict__["profession_text"] in roles.keys():
            input_text += f'CREATE ({people_new_name[person.__dict__["staff_id"]]})-[:{roles[person.__dict__["profession_text"]]}]->({new_film_names[film]}) '
        elif person.__dict__["profession_text"] == "Актеры":
            input_text += f'CREATE ({people_new_name[person.__dict__["staff_id"]]})-[:ACTED_IN '
            input_text += "{"
            input_text += f'roles:["{person.__dict__["description"]}"]'
            input_text += "}"
            input_text += f']->({new_film_names[film]}) '






final = open("final.txt", "w", encoding = "utf-8")
final.write(input_text)
final.close()




graph = Graph("bolt://localhost:7687", auth=("GGG", "123456789"))
graph.run(input_text)