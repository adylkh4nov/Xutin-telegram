from bot import bot

if __name__ == "__main__":
    while True:
        try:
            bot.polling()
        except Exception as e:
            print(e)