#!/usr/bin/env python

"""
Simple Bot to send timed Telegram messages.

This Bot uses the Updater class to handle the bot and the JobQueue to send
timed messages.

First, a few handler functions are defined. Then, those functions are passed to
the Dispatcher and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.

Usage:
Basic Alarm Bot example, sends a message after a set time.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

import logging

from telegram import Update
from miner_utils import *
from telegram.ext import Updater, CommandHandler, CallbackContext

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)
latest_state_of_incorrect_shares = ''


# Define a few command handlers. These usually take the two arguments update and
# context. Error handlers also receive the raised TelegramError object in error.
def stats(update: Update, _: CallbackContext) -> None:
    update.message.reply_text(scan_logfile_for_stats())


def have_incorrect_shares_changed() -> bool:
    global latest_state_of_incorrect_shares
    if scan_logfile_for_incorrect_shares() != latest_state_of_incorrect_shares:
        latest_state_of_incorrect_shares = scan_logfile_for_incorrect_shares()
        return True
    else:
        return False


def notify_on_issue(context: CallbackContext) -> None:
    """Send the notification message."""
    job = context.job
    if not check_if_process_running():
        context.bot.send_message(job.context, text='Miner process not found. Restarting rig')
        os.system('shutdown /r')
    if have_incorrect_shares_changed():
        context.bot.send_message(job.context, text=latest_state_of_incorrect_shares)


def remove_job_if_exists(name: str, context: CallbackContext) -> bool:
    """Remove job with given name. Returns whether job was removed."""
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True


def set_watchdog_monitor(update: Update, context: CallbackContext) -> None:
    """Add a job to the queue."""
    chat_id = update.message.chat_id
    try:
        # args[0] should contain the time for the timer in seconds, if not provided defaults to 60 seconds
        due = int(context.args[0]) if len(context.args) == 1 else 60
        if due < 0:
            update.message.reply_text("Sorry the interval can't be negative!")
            return

        job_removed = remove_job_if_exists(str(chat_id), context)
        context.job_queue.run_repeating(notify_on_issue, interval=due, context=chat_id, name=str(chat_id))

        text = 'Watchdog monitor successfully set for ' + str(due) + 'seconds interval.'
        if job_removed:
            text += ' Old one was removed.'
        update.message.reply_text(text)

    except (IndexError, ValueError):
        update.message.reply_text('Usage: /monitor <seconds>')


def unset(update: Update, context: CallbackContext) -> None:
    """Remove the job if the user changed their mind."""
    chat_id = update.message.chat_id
    job_removed = remove_job_if_exists(str(chat_id), context)
    text = 'Timer successfully cancelled!' if job_removed else 'You have no active timer.'
    update.message.reply_text(text)


def restart_rig(update: Update, _: CallbackContext) -> None:
    update.message.reply_text("restarting now.")
    os.system("shutdown /r")


def main() -> None:
    """Run bot."""
    # Create the Updater and pass it your bot's token.
    updater = Updater(os.getenv('TELEGRAM_BOT_TOKEN'))

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("stats", stats))
    dispatcher.add_handler(CommandHandler("monitor", set_watchdog_monitor))
    dispatcher.add_handler(CommandHandler("unset", unset))
    dispatcher.add_handler((CommandHandler("restart", restart_rig)))

    # Start the Bot
    updater.start_polling()

    # Block until you press Ctrl-C or the process receives SIGINT, SIGTERM or
    # SIGABRT. This should be used most of the time, since start_polling() is
    # non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
