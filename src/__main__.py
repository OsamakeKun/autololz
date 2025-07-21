import logging
import time
from typing import List, Tuple

from src.config import Config
from src.market import MarketAPI, MarketBuyError, MarketItem
from src.market.api import parse_search_data
from src.telegram import TelegramAPI

TELEGRAM_MESSAGE = (
    '🎊 Приобретен аккаунт: <a href="https://lzt.market/{item_id}">{title}</a>\n'
    "💲 Цена: <code>{price}₽</code>\n"
    '👷 Продавец: <a href="https://lolz.live/members/{seller_id}">{seller_username}</a>'
)


def main():
    config = Config.load_config("config.ini")

    logging.basicConfig(
        level=getattr(logging, config.logging.level.upper(), logging.INFO),
        format=config.logging.format,
    )

    telegram = TelegramAPI(config.telegram.bot_token)
    market = MarketAPI(config.lolzteam.token)
    count_purchase = 0

    searches: List[Tuple[str, dict]] = []
    for search_url in config.lolzteam.search_urls_list:
        category, params = parse_search_data(search_url)
        searches.append((category, params))

    while True:
        for category, params in searches:
            try:
                search_result = market.search(category, params)
                items = search_result.get("items", [])
            except Exception as e:
                logging.error("Ошибка при поиске аккаунтов: %s", e)
                continue

            logging.info(
                "По запросу '%s' с параметрами %s найдено %d аккаунтов",
                category,
                params,
                len(items),
            )

            for item in items:
                item_id = item.get("item_id")
                if not item_id:
                    logging.warning("У объекта нет item_id, пропускаю")
                    continue

                market_item = MarketItem(item, config.lolzteam.token)
                try:
                    logging.info("Пытаюсь купить аккаунт %s", item_id)
                    market_item.fast_buy()
                except MarketBuyError as error:
                    logging.warning(
                        "Ошибка при покупке аккаунта %s: %s",
                        item_id,
                        error.message,
                    )
                    continue
                except Exception as e:
                    logging.error(
                        "Неожиданная ошибка при покупке аккаунта %s: %s",
                        item_id,
                        e,
                    )
                    continue
                else:
                    logging.info("Аккаунт %s успешно куплен!", item_id)
                    count_purchase += 1

                    account_object = market_item.item_object
                    seller = account_object.get("seller", {})

                    telegram.send_message(
                        TELEGRAM_MESSAGE.format(
                            item_id=item_id,
                            title=account_object.get("title", "Нет названия"),
                            price=account_object.get("price", "N/A"),
                            seller_id=seller.get("user_id", "0"),
                            seller_username=seller.get("username", "Неизвестен"),
                        ),
                        chat_id=config.telegram.id,
                        parse_mode="HTML",
                    )

                    if count_purchase >= config.lolzteam.count:
                        logging.info(
                            "Успешно куплено %d аккаунтов, завершаю работу.",
                            count_purchase,
                        )
                        return
                    break

        # Вот ключевое изменение: используем getattr с дефолтом
        poll_interval = getattr(config.lolzteam, "poll_interval_seconds", 3)
        time.sleep(poll_interval)


if __name__ == "__main__":
    main()
