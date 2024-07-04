import mysql.connector

cnx = mysql.connector.connect(
    host = "localhost",
    user = "root",
    password = "root",
    database = "onis_eatery" 
)

def get_order_status(order_id : int):
    cursor = cnx.cursor()
    
    query = ("select _status from delivery where order_id = %s")
    
    cursor.execute(query, (order_id,))
    
    result = cursor.fetchone()
    
    cursor.close()
    
    if result is not None:
        return result[0]
    
    else:
        return None
    
def get_food_prices(food_items: list):
    
    food_prices = {}
    
    for food in food_items:
        query = ("select food_price from onis_eatery.food_items where food_name = %s")
        cursor = cnx.cursor()
        cursor.execute(query, (food,))
        result = cursor.fetchone()
        cursor.close()
        if result is not None:
            food_prices[food] = float(result[0])
            
    return food_prices

def get_food_id(food_item : str):
    query = ("select food_id from onis_eatery.food_items where food_name = %s")
    cursor = cnx.cursor()
    cursor.execute(query, (food_item,))
    result = cursor.fetchone()
    cursor.close()
    if result is not None:
        return result[0]
    
    
def get_next_order_id():
    cursor = cnx.cursor()
    
    query = ("SELECT MAX(order_id) FROM orders")
    cursor.execute(query)
    result = cursor.fetchone()[0]
    
    cursor.close()
    
    if result is None:
        return 1
    
    else:
        return result + 1
    
def insert_new_order(order_id, food_name,quantity,food_price,_date):
    food_id = get_food_id(food_name)
    try:
        cursor = cnx.cursor()
        insert_query = """
        INSERT INTO orders
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        data = (order_id, food_id, food_name,quantity,food_price,_date)
        cursor.execute(insert_query, data)
        cnx.commit()
        cursor.close()
        return True
    except:
        return False
    
def insert_new_delivery(order_id , status, _date):
    # try:
    cursor = cnx.cursor()
    insert_query = """
    INSERT INTO delivery
    VALUES (%s, %s, %s)
    """
    data = (order_id, status,_date)
    cursor.execute(insert_query, data)
    cnx.commit()
    cursor.close()
    #     return True
    # except:
    #     return False
    

if __name__ == "__main__":
    print(get_food_prices(["Moin moin"]))
