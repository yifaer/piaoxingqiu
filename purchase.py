import yaml
import requests
import urllib3
from piaoxingqiu import Piaoxingqiu

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class Purchase:
    def __init__(self) -> None:
        self.Piaoxingqiu = Piaoxingqiu()

        with open('requirement.yaml', 'r', encoding='utf-8') as config_file:
            config = yaml.load(config_file, Loader=yaml.FullLoader)

        self.show = {
            'show_id': config['Show']['show_id'],
            'session_id': config['Show']['session_id'],
            'session_id_exclude': [],
            'seat_plan_id': config['Show']['seat_plan_id'],
            'price': 0
        }

        self.bill = {
            'buy_count': config['Bill']['buy_count'],
            'deliver_method': config['Bill']['deliver_method']
        }

        self.audiences = [audience for audience in config['Audience']]

    # ========================= 初始化观影人 =========================
    def pre_purchase(self, token) -> None:

        print("========== 初始化观影人 ==========")

        self.Piaoxingqiu.initialize_audience(token, self.audiences)

        self.audiences = self.Piaoxingqiu.get_audiences(token)
        print("audiences:", self.audiences)

        if self.bill['buy_count'] > len(self.audiences):
            raise Exception("购票数量大于观演人数量")

        self.bill['audience_ids'] = [a["id"] for a in self.audiences]

        print("audience_ids:", self.bill['audience_ids'])

        # seat
        if self.show['session_id']:
            self.seat_plans = self.Piaoxingqiu.get_seat_plans(
                self.show['show_id'],
                self.show['session_id']
            )

    # ========================= 购买流程 =========================
    def purchase(self, token) -> bool:
        # ================= session选择 =================
        if not self.show['session_id']:

            print("========== 获取session ==========")

            while True:
                sessions = self.Piaoxingqiu.get_sessions(self.show['show_id'])

                if sessions:
                    for s in sessions:

                        status = s.get("sessionStatus") or s.get("status")
                        session_id = s.get("bizShowSessionId")

                        print("👉 session:", session_id, "status:", status)

                        if status in ["ON_SALE", "onsale", "1", 1]:
                            self.show['session_id'] = session_id
                            print("✔ 命中session:", session_id)
                            break

                if self.show['session_id']:
                    break
                else:
                    print("❌ 没有可用session，继续刷新...")

        # ================= seat + price 选择 =================
        if not self.show['seat_plan_id']:

            print("========== 获取seat ==========")

            while True:

                # ✔ 只请求一次
                self.seat_plans = self.Piaoxingqiu.get_seat_plans(
                    self.show['show_id'],
                    self.show['session_id']
                )

                self.seat_count = self.Piaoxingqiu.get_seat_count(
                    self.show['show_id'],
                    self.show['session_id']
                )

                selected_seat = None

                # ================= 找可购买 seat =================
                for seat in self.seat_count:

                    can_buy = seat.get("canBuyCount", 0)
                    print("👉 seat:", seat)

                    if can_buy >= self.bill['buy_count']:
                        selected_seat = seat.get("seatPlanId")
                        self.show['seat_plan_id'] = selected_seat
                        print("✔ 命中seat:", selected_seat)
                        break

                if self.show['seat_plan_id']:

                    # ================= 关键：从 seat_plans 取 price =================
                    self.show['price'] = None

                    for sp in self.seat_plans:
                        if sp.get("seatPlanId") == self.show['seat_plan_id']:
                            self.show['price'] = (
                                sp.get("originalPrice")
                                or sp.get("seatPlanPrice")
                            )
                            break

                    print("✔ 选中price:", self.show['price'])

                    # 🚨 强校验（防止再次 None）
                    if not self.show['price']:
                        print("❌ price 仍为空，重新刷新seat...")
                        self.show['seat_plan_id'] = None
                        continue

                    break

                else:
                    print("❌ 没有符合seat，继续刷新...")

        # ================= deliver =================
        if not self.bill['deliver_method']:

            self.bill['deliver_method'] = self.Piaoxingqiu.get_deliver_method(
                token,
                self.show['show_id'],
                self.show['session_id'],
                self.show['seat_plan_id'],
                self.show['price'],
                self.bill['buy_count']
            )

            print("deliver_method:", self.bill['deliver_method'])

        # ================= 下单 =================
        print("========== 下单前最终参数 ==========")
        print("session:", self.show['session_id'])
        print("seat:", self.show['seat_plan_id'])
        print("price:", self.show['price'])
        print("audience:", self.bill.get('audience_ids'))
        print("deliver:", self.bill['deliver_method'])

        if self.bill['deliver_method'] == "VENUE_E":

            order_status = self.Piaoxingqiu.create_order(
                token,
                self.show['show_id'],
                self.show['session_id'],
                self.show['seat_plan_id'],
                self.show['price'],
                self.bill['buy_count'],
                self.bill['deliver_method'],
                0, None, None, None, None, None, []
            )

        elif self.bill['deliver_method'] == "EXPRESS":

            address = self.Piaoxingqiu.get_address(token)

            express_fee = self.Piaoxingqiu.get_express_fee(
                token,
                self.show['show_id'],
                self.show['session_id'],
                self.show['seat_plan_id'],
                self.show['price'],
                self.bill['buy_count'],
                address["locationId"]
            )

            order_status = self.Piaoxingqiu.create_order(
                token,
                self.show['show_id'],
                self.show['session_id'],
                self.show['seat_plan_id'],
                self.show['price'],
                self.bill['buy_count'],
                self.bill['deliver_method'],
                express_fee["priceItemVal"],
                address["username"],
                address["cellphone"],
                address["addressId"],
                address["detailAddress"],
                address["locationId"],
                self.bill['audience_ids']
            )

        else:

            order_status = self.Piaoxingqiu.create_order(
                token,
                self.show['show_id'],
                self.show['session_id'],
                self.show['seat_plan_id'],
                self.show['price'],
                self.bill['buy_count'],
                self.bill['deliver_method'],
                0,
                None, None, None, None, None,
                self.bill['audience_ids']
            )

        print("order_status:", order_status)

        return order_status

# ========================= main =========================
if __name__ == '__main__':

    with open('account.yaml', 'r', encoding='utf-8') as config_file:
        config = yaml.load(config_file, Loader=yaml.FullLoader)

    accounts = [{'token': account['token']} for account in config['Account']]

    instance = Purchase()

    instance.pre_purchase(accounts[0]['token'])

    while True:
        try:
            if instance.purchase(accounts[0]['token']):
                print("✔ 成功下单")
                break
        except Exception as e:
            print("❌ 错误:", e)
            break