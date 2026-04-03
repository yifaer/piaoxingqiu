import requests
import urllib3

# 关闭SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def req(method, url, **kwargs):
    kwargs["verify"] = False
    return requests.request(method, url, **kwargs)


class Piaoxingqiu:
    def __init__(self) -> None:
        pass

    def initialize_audience(self, token, audiences) -> None:
        """编辑观影人"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Mobile Safari/537.36',
            'Content-Type': 'application/json',
            'access-token': token
        }

        url = "https://m.piaoxingqiu.com/cyy_gatewayapi/user/buyer/v3/user_audiences"

        # 删除观影人
        audiences_to_delete = self.get_audiences(token)

        if audiences_to_delete:
            for audience in audiences_to_delete:
                delete_url = f"{url}/{audience['id']}"
                resp = req("DELETE", delete_url, headers=headers).json()

                if resp.get("statusCode") != 200:
                    raise Exception("删除失败：" + str(resp))

        after = self.get_audiences(token)

        if after is None or len(after) == 0:
            print("删除观影人成功！")
        else:
            raise Exception("删除观影人失败：" + str(after))

        # 添加观影人
        for audience in audiences:
            response = req("POST", url, headers=headers, json=audience).json()
            if response["statusCode"] == 200:
                print(f"添加观影人（{audience['name']}）成功！")
            else:
                raise Exception("添加观影人失败：" + str(response))

    def get_show(self, show_id) -> dict | None:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N)',
            'Content-Type': 'application/json'
        }

        url = f"https://m.piaoxingqiu.com/cyy_gatewayapi/show/pub/v3/show/{show_id}/sessions_from_marketing_countdown"

        response = req("GET", url, headers=headers).json()

        if response["statusCode"] != 200:
            raise Exception("get_show异常:" + str(response))

        show = {
            'show_name': response['data']['showName'],
            'show_id': response['data']['showId'],
            'sessions': {
                session['bizShowSessionId']: {
                    'session_id': session['bizShowSessionId'],
                    'session_date': session['sessionName']
                }
                for session in response['data']['sessionVOs']
            }
        }

        for session_id in show['sessions']:
            url = f"https://m.piaoxingqiu.com/cyy_gatewayapi/show/pub/v3/show/{show_id}/show_session/{session_id}/seat_plans_static_data"
            response = req("GET", url, headers=headers).json()

            show['sessions'][session_id]['seat_plans'] = {
                seat_plan['seatPlanId']: {
                    'seat_plan_id': seat_plan['seatPlanId'],
                    'seat_plan_price': seat_plan['originalPrice'],
                    'seat_plan_name': seat_plan['seatPlanName']
                }
                for seat_plan in response['data']['seatPlans']
            }

        return show

    def get_sessions(self, show_id) -> list | None:
        url = f"https://m.piaoxingqiu.com/cyy_gatewayapi/show/pub/v3/show/{show_id}/sessions_dynamic_data"
        response = req("GET", url).json()

        if response["statusCode"] == 200:
            return response["data"]["sessionVOs"]

        print("get_sessions异常:" + str(response))
        return None

    def get_seat_plans(self, show_id, session_id) -> list:
        url = f"https://m.piaoxingqiu.com/cyy_gatewayapi/show/pub/v3/show/{show_id}/show_session/{session_id}/seat_plans_static_data"
        response = req("GET", url).json()

        if response["statusCode"] == 200:
            return response["data"]["seatPlans"]

        raise Exception("get_seat_plans异常:" + str(response))

    def get_seat_count(self, show_id, session_id) -> list:
        url = f"https://m.piaoxingqiu.com/cyy_gatewayapi/show/pub/v3/show/{show_id}/show_session/{session_id}/seat_plans_dynamic_data"
        response = req("GET", url).json()

        if response["statusCode"] == 200:
            return response["data"]["seatPlans"]

        raise Exception("get_seat_count异常:" + str(response))

    def get_deliver_method(self, token, show_id, session_id, seat_plan_id, price: int, qty: int) -> str:
        headers = {
            'User-Agent': 'Mozilla/5.0',
            'Content-Type': 'application/json',
            'access-token': token
        }

        data = {
            "items": [{
                "skus": [{
                    "seatPlanId": seat_plan_id,
                    "sessionId": session_id,
                    "showId": show_id,
                    "skuId": seat_plan_id,
                    "skuType": "SINGLE",
                    "ticketPrice": price,
                    "qty": qty
                }],
                "spu": {"id": show_id, "spuType": "SINGLE"}
            }]
        }

        url = "https://m.piaoxingqiu.com/cyy_gatewayapi/trade/buyer/order/v3/pre_order"
        response = req("POST", url, headers=headers, json=data).json()

        if response["statusCode"] == 200:
            return response["data"]["supportDeliveries"][0]["name"]

        raise Exception("获取门票类型异常:" + str(response))

    def get_audiences(self, token) -> list | None:
        headers = {
            'User-Agent': 'Mozilla/5.0',
            'Content-Type': 'application/json',
            'access-token': token
        }

        url = "https://m.piaoxingqiu.com/cyy_gatewayapi/user/buyer/v3/user_audiences"
        response = req("GET", url, headers=headers).json()

        if response["statusCode"] == 200:
            return response["data"]

        print("get_audiences异常:" + str(response))
        return None

    def get_address(self, token):
        headers = {
            'User-Agent': 'Mozilla/5.0',
            'Content-Type': 'application/json',
            'access-token': token
        }

        url = "https://m.piaoxingqiu.com/cyy_gatewayapi/user/buyer/v3/user/addresses/default"
        response = req("GET", url, headers=headers).json()

        if response["statusCode"] == 200:
            return response["data"]

        raise Exception("get_address异常:" + str(response))

    def get_express_fee(self, token, show_id, session_id, seat_plan_id, price: int, qty: int, location_city_id: str):
        headers = {
            'User-Agent': 'Mozilla/5.0',
            'Content-Type': 'application/json',
            'access-token': token
        }

        data = {
            "items": [{
                "skus": [{
                    "seatPlanId": seat_plan_id,
                    "sessionId": session_id,
                    "showId": show_id,
                    "skuId": seat_plan_id,
                    "skuType": "SINGLE",
                    "ticketPrice": price,
                    "qty": qty,
                    "deliverMethod": "EXPRESS"
                }],
                "spu": {"id": show_id, "spuType": "SINGLE"}
            }],
            "locationCityId": location_city_id
        }

        url = "https://m.piaoxingqiu.com/cyy_gatewayapi/trade/buyer/order/v3/price_items"
        response = req("POST", url, headers=headers, json=data).json()

        if response["statusCode"] == 200:
            return response["data"][0]

        raise Exception("获取快递费异常:" + str(response))

    def create_order(self, token, show_id, session_id, seat_plan_id, price: int, qty: int,
                     deliver_method, express_fee: int, receiver, cellphone,
                     address_id, detail_address, location_city_id, audience_ids: list):

        headers = {
            'User-Agent': 'Mozilla/5.0',
            'Content-Type': 'application/json',
            'access-token': token
        }

        data = {
            "priceItemParam": [{
                "priceItemName": "票款总额",
                "priceItemVal": price * qty,
                "priceItemType": "TICKET_FEE",
                "direction": "INCREASE",
            }],
            "items": [{
                "skus": [{
                    "seatPlanId": seat_plan_id,
                    "sessionId": session_id,
                    "showId": show_id,
                    "skuId": seat_plan_id,
                    "skuType": "SINGLE",
                    "ticketPrice": price,
                    "qty": qty,
                    "deliverMethod": deliver_method
                }],
                "spu": {"id": show_id, "spuType": "SINGLE"}
            }],
            "contactParam": {
                "receiver": receiver,
                "cellphone": cellphone
            },
            "one2oneAudiences": [{"audienceId": i, "sessionId": session_id} for i in audience_ids]
        }

        url = "https://m.piaoxingqiu.com/cyy_gatewayapi/trade/buyer/order/v3/create_order"
        response = req("POST", url, headers=headers, json=data).json()

        if response["statusCode"] == 200:
            print("下单成功！")
            return True

        raise Exception("下单异常:" + str(response))