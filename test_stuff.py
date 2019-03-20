import datetime


def get_start_and_end_date_from_calendar_week(year, calendar_week):
    monday = datetime.datetime.strptime(f'{year}-{calendar_week}-0',
                                        "%Y-%W-%w").date()
    return monday, monday + datetime.timedelta(days=6)


if __name__ == "__main__":
    print(get_start_and_end_date_from_calendar_week(datetime.datetime.now(

    ).year, 47))
