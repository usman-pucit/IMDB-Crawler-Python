from multiprocessing import Pool
import requests
from bs4 import BeautifulSoup
import re
import operator


# Constants


# base url
base_url = 'https://www.imdb.com/chart/moviemeter?ref_=nv_mv_mpm'

# properties
all_urls = list()
genre_list = {}
genre_count = {}

highest_rated_genre = ""

# CSV file names
movie_info_file = "favourite_imdb_movies.csv"
trending_movies_file = "trending_movies.csv"
previous_week_position_file = "previous_week_position.csv"

# CSV file headers
movie_info_headers = "current_position;popularity;budget;number_of_views;number_of_critics;genre\n"
trending_movies_header = "movie_name;popularity_increase \n"
previous_week_position_headers = "movie_name;popularity \n"


# ------------------------------------------------- Main Section --------------------------------------- #

# extracting all urls to grab content
def generate_urls():

    global genre_list
    # request connection, grabbing content
    source_text = requests.get(base_url).text

    # reading text as html
    soup_data = BeautifulSoup(source_text, 'html5lib')

    # extracting table content
    container = soup_data.find('table', attrs={'class': 'chart full-width'})

    for link in container.find_all('a', href=True):
        all_urls.append("https://www.imdb.com"+link['href'])


# def: writing csv headers
def writing_csv_file_headers():

    # writing movies info csv file headers
    file_writer(movie_info_file, movie_info_headers, "w")

    # writing trending movies csv file headers
    file_writer(trending_movies_file, trending_movies_header, "w")

    # writing previous week movies csv file headers
    file_writer(previous_week_position_file, previous_week_position_headers, "w")


# def: crawling, grabbing content
def scrape(url):

    # request to grab content
    source = requests.get(url)

    # bs extracting content
    data = BeautifulSoup(source.text, 'html5lib')

    # extracting information
    movie_information(data)


# def: extracting movies required info
def movie_information(data):

    # main container
    movie_info_container = data.find('div', class_='heroic-overview')

    # summary container
    plot_summary_wrapper = movie_info_container.find('div', class_='plot_summary_wrapper')

    # Section 1:

    # movie ranking & popularity
    # 1,2:
    ranking = func_to_get_popularity(plot_summary_wrapper)

    # 3:
    # budget = movie_budget(data)

    # total views
    # 5
    total_user_views = func_to_total_user_views(movie_info_container)

    # user reviews & critics
    # 5
    user_reviews = func_to_get_user_reviews(plot_summary_wrapper)

    # genre of movie
    # 6:
    genre = func_to_get_movie_genre(movie_info_container)

    # Section 2 methods:

    # movies with improved rating
    # 1:
    movies_with_improved_rating(movie_info_container, plot_summary_wrapper)

    # movies previous week rating
    # 2:
    previous_week_movies_position(ranking, movie_info_container)

    # making genre list
    make_genre_list(ranking, genre)

    # CSV file for section 1:
    # preparing movie info
    prepare_movie_info(ranking, "", user_reviews, total_user_views, genre)


# def: setting up movie info
def prepare_movie_info(ranking, budget, user_reviews, user_views, genre):

    # movie info
    movie_info_string = str(ranking[0]) + ";" + str(ranking[1])
    movie_info_string = movie_info_string + ";" + budget + ";"
    movie_info_string = movie_info_string + str(user_reviews[0]) + ";" + str(user_reviews[1])
    movie_info_string = movie_info_string + ";" + str(user_views) + ";" + genre + "\n"

    # CSV file writing for section 1:
    file_writer(movie_info_file, movie_info_string, "a")


# def: CSV file writer
def file_writer(file, value, action):

    file_writer = open(file, action)
    file_writer.write(value)
    file_writer.close()

# ----------------------------------------------- SECTION 1 ----------------------------------------- #


# def: get movie popularity or ranking
# 1,2:
def func_to_get_popularity(data):

    title_review_bar = data.find('div', class_='titleReviewBar')
    ranking = "0.0"
    popularity = "0.0"

    if title_review_bar is not None:
        title_review_bar_item = title_review_bar.find_all('div', class_='titleReviewBarItem')
        if title_review_bar_item is not None:
            popularity_item = title_review_bar_item[-1]
            popularity_div = popularity_item.find('div', class_='titleReviewBarSubItem')

            if popularity_div is not None:
                popularity_span = popularity_div.find('span', class_='subText')
                if popularity_span is not None:
                    popularity_span_text = re.sub("[\(\[].*?[\)\]]", "", popularity_span.text)
                    popularity_span_text = popularity_span_text.replace('(', '').replace(')', '')
                    ranking = popularity_span_text.replace('\n', ' ').replace('\r', '').replace(' ', '')

                    popularity = func_to_get_popularity_rise_or_fall(popularity_div)

    return [ranking, popularity]


# def: get movie popularity rise or fall
def func_to_get_popularity_rise_or_fall(popularity_div):

    if popularity_div.find('span', class_='popularityUpOrFlat') is not None:
        up = popularity_div.find('span', class_='popularityUpOrFlat')
        return "+"+up.text

    elif popularity_div.find('span', class_='popularityDown') is not None:
        down = popularity_div.find('span', class_='popularityDown')
        return "-"+down.text


# movie budget
def movie_budget(data):
    main_bottom_div = data.find("div", attrs={"class": "main", "id": "main_bottom"})
    budget_main_div = main_bottom_div.find("div", attrs={"class": "article", "id": "titleDetails"})
    budget_all_divs = budget_main_div.find_all("div", attrs={"class": "txt-block"})

    return budget_all_divs[6].text.replace('(estimated)', '').replace('Budget:', '')


# getting user reviews on movie
# 5
def func_to_get_user_reviews(data):

    review_div = data.find('div', class_='titleReviewBarItem titleReviewbarItemBorder')

    list_reviews = list()

    if review_div is not None:
        if review_div.find('span', class_='subText') is not None:
            review_span = review_div.find('span', class_='subText')
            p_tags = review_span.find_all('a')
            for item in p_tags:
                if "user" in item.text:
                    string = item.text.replace('user', '').replace(' ', '')
                    list_reviews.append(string)
                elif "critic" in item.text:
                    string = item.text.replace('critic', '').replace(' ', '')
                    list_reviews.append(string)

    if len(list_reviews) == 0:
        list_reviews.append("None")
        list_reviews.append("None")
    elif len(list_reviews) == 1:
        list_reviews.append("None")

    return list_reviews


# getting total user views
# 4
def func_to_total_user_views(data):

    title_bar_wrapper = data.find('div', class_='title_bar_wrapper')
    imdb_rating = title_bar_wrapper.find('div', class_='imdbRating')

    user_views = "None"
    if imdb_rating is not None:
        rating_users_count = imdb_rating.find_all('a', href=True)
        if len(rating_users_count) > 0:
            user_views = rating_users_count[0].text

    return user_views


# def: getting movie genre
# 6:
def func_to_get_movie_genre(data):

    title_bar_wrapper = data.find('div', class_='title_bar_wrapper')
    title_wrapper = title_bar_wrapper.find('div', class_='title_wrapper')
    subtext = title_wrapper.find('div', class_='subtext')

    return subtext.a.text


# ---------------------------------------------- SECTION 2 ------------------------------------------ #

# Section 2:

# def: movies with improved rating

def movies_with_improved_rating(data, popularity_div):

    title_bar_wrapper = data.find('div', class_='title_bar_wrapper')
    title_wrapper = title_bar_wrapper.find('div', class_='title_wrapper')
    title_header = title_wrapper.find('h1')

    if popularity_div.find('span', class_='popularityUpOrFlat') is not None:
        up = popularity_div.find('span', class_='popularityUpOrFlat')

        file_writer(trending_movies_file, title_header.text + ";" + "+" + up.text + "\n", "a")


# def: previous week movies rating

def previous_week_movies_position(ranking, data):

    title_bar_wrapper = data.find('div', class_='title_bar_wrapper')
    title_wrapper = title_bar_wrapper.find('div', class_='title_wrapper')
    title_header = title_wrapper.find('h1')

    rating = ranking[0]
    rise_or_fall = ranking[1]

    previous_week_position = ""

    if rise_or_fall is not None:
        if "+" in rise_or_fall:
            rise_or_fall = rise_or_fall.replace('+', '')
            previous_week_position = str(int(float(rating)) + int(float(rise_or_fall)))
        elif "-" in rise_or_fall:
            rise_or_fall = rise_or_fall.replace('-', '')
            previous_week_position = str(int(float(rating)) - int(float(rise_or_fall)))

    file_writer(previous_week_position_file, title_header.text+";"+previous_week_position + "\n", "a")


# def: genre listing with ranking
# 3:
def make_genre_list(ranking, genre):

    if genre in genre_list:
        old_value = genre_list.get(genre)
        new_value = float(ranking[0])
        old_count = genre_count.get(genre)

        if str(old_value + new_value) is not None:
            genre_list.pop(genre)
            genre_list.setdefault(genre, (old_value + new_value) / old_count + 1)

            genre_count.pop(genre)
            genre_count.setdefault(genre, old_count + 1)

            highest_rated_genre(genre_list)

    else:
        genre_list.setdefault(genre, float(ranking[0]))
        genre_count.setdefault(genre, 1)


# def: printing highest rated genre
# 3:

def highest_rated_genre(list):
    highest_rated_genre = max(list.items(), key=operator.itemgetter(1))[0]
    print("Highest Rated Genre : "+str(highest_rated_genre))


# main function
generate_urls()


# writing CSV headers
writing_csv_file_headers()

# section 1
# crawling and spider request
p = Pool(5)
p.map(scrape, all_urls)
p.terminate()
p.join()



