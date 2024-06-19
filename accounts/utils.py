import datetime



def users_id_generator(user_id):
    current_datetime = datetime.datetime.now().strftime('%Y%m%d%H%M%S')#202212281059 
    users_id = current_datetime + str(user_id)
    print(users_id)
    return users_id