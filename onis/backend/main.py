from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import backend.db as db
import backend.helper as helper
from datetime import datetime

app = FastAPI()

inprogress_orders = {}


@app.post("/")
async def handle_request(request: Request):
    payload = await request.json()

    intent = payload["queryResult"]["intent"]["displayName"]
    query_text = payload["queryResult"]["queryText"]
    parameters = payload["queryResult"]["parameters"]
    output_contexts = payload["queryResult"]["outputContexts"]

    session_id = helper.extract_session_id(output_contexts[0]["name"])

    intent_handler_dict = {
        "track.order - context: ongoing-tracking": track_order,
        "order.add - context: ongoing-order": add_order,
        "order.complete - context: ongoing-order": comfirm_order,
        "order.comfirm - context: completing-order" : place_order,
        "order.remove - context: ongoing-order" : remove_from_current_order
    }

    return intent_handler_dict[intent](query_text,parameters, session_id)


def track_order(query_text : str, parameters: dict, session_id: str):
    order_id = int(parameters["number"])

    status = db.get_order_status(order_id)
    if status:
        fulfillment_text = f"The status for your order is {status}."
    else:
        fulfillment_text = (
            f"we could not find an order corresponding to this order id #{order_id}"
        )

    return JSONResponse(content={"fulfillmentText": fulfillment_text})


def add_order(query_text : str,parameters: dict, session_id: str):
    food = parameters["food-item"]
    quantity = parameters["number"]

    if len(food) != len(quantity):
        fulfillment_text = "Sorry. Please can you specify the food and quantity also"
    else:
        new_food_dict = dict(zip(food, quantity))
        if session_id in inprogress_orders:
            current_food_dict = inprogress_orders[session_id]
            current_food_dict.update(new_food_dict)
            inprogress_orders[session_id] = current_food_dict

        else:
            inprogress_orders[session_id] = new_food_dict

        order_str = helper.get_str_from_food_dict(inprogress_orders[session_id])

        fulfillment_text = f"got it! {order_str}. Anything else?"

    return JSONResponse(content={"fulfillmentText": fulfillment_text})


def comfirm_order(query_text : str,parameters: dict, session_id: str):
    if session_id not in inprogress_orders:
        fulfillment_text = "So sorry! I'm having problems finding your order. Please can you place your order again?"

    else:
        # full_details = {}
        full_details = []
        total_price = 0
        orders = inprogress_orders[session_id]
        food_prices = db.get_food_prices(orders.keys())
        for order in orders.keys():
            total_price += food_prices[order] * orders[order]
            full_details.append(f"{int(orders[order])} {order} which costs a total of ₦{int(food_prices[order] * orders[order])} each is ₦{int(food_prices[order])} ")
        d = " ,".join(i for i in full_details)
        fulfillment_text = f"Here's your order details {d}. \nYour to order costs a total of ₦{int(total_price)}, \nwould you like to place your order?"

    return JSONResponse(content={"fulfillmentText": fulfillment_text})

def place_order(query_text : str,parameters: dict, session_id: str):
    if query_text.lower() == "no":
        fulfillment_text = "your order has not been placed"
    elif query_text.lower() == "yes":
        try:
            order_id = save_to_db(inprogress_orders[session_id])
            fulfillment_text = f"your order has been placed, Heres your order id: {order_id}"
        except:
            fulfillment_text = "your order has not been placed"
    else:
        fulfillment_text = f"So sorry! what did you say? should i place the order? answer 'yes' or 'no {query_text.lower()}"
    return JSONResponse(content={"fulfillmentText": fulfillment_text})

def remove_from_current_order(query_text : str,parameters: dict, session_id: str):
    if session_id not in inprogress_orders:
        fulfillment_text = f"Having problem finding your order, can you please place a new order?"
    
    else:
        current_order = inprogress_orders[session_id]
        food_items = parameters["food-item"]
        
        removed_items = []
        no_food_items = []
        
        for food in food_items:
            if food not in current_order:
                no_food_items.append(food)
            else:
                removed_items.append(food)
                del current_order[food] 
        
        if len(removed_items) > 0:
            fulfillment_text = f"Removed {' ,'.join(removed_items)} from your order"
        
        if len(no_food_items) > 0:
            fulfillment_text = f"Your current order does not have {' ,'.join(no_food_items)}"
            
        if len(current_order.keys()) == 0:
            fulfillment_text += ". your order is empty!"
            
        else:
            order_str = helper.get_str_from_food_dict(current_order)
            fulfillment_text += f"Here is what is left in your order: {order_str}. Is that all?"
            
    return JSONResponse(content={"fulfillmentText": fulfillment_text})
        
def save_to_db(orders : dict):
    order_id = db.get_next_order_id()
    food_prices = db.get_food_prices(orders.keys())
    for food, quantity in orders.items():
        price = int(food_prices[food] * quantity)
        db.insert_new_order(order_id,food,quantity,price,datetime.now())
    done = db.insert_new_delivery(order_id,"in progress", datetime.now())
    return order_id