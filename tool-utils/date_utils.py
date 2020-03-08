class NextDate(object):
    def __init__(self,year=1,month=1,day=1,weekday=0,yearday=1):
        self.year = year # >0
        self.month = month #1~12
        self.day = day #1~31
        self.weekday = weekday
        self.yearday = yearday
    def is_leap_year(self):
        # 判断当前年份是否是闰年
        return (self.year % 4 == 0 and self.year % 100 != 0) or self.year % 400 == 0
    def max_day(self):
        # 计算本月最大的一天
        # 闰年2月29天，否则28天
        if self.is_leap_year():
            m2d = 29
        else :
            m2d = 28
        days = [31,m2d,31,30,31,30,31,31,30,31,30,31]
        return days[self.month-1]
    def add_a_month(self):
        # 当前日期对象自增一月，不考虑日
        # 超过12月，年加1
        if self.month == 12:
            self.year = self.year+1
            self.yearday = 1
            self.month = 1
        else :
            self.month = self.month+1
    def add_a_day(self):
        # 星期
        self.weekday += 1
        if self.weekday >= 7:
            self.weekday = 0
        self.yearday += 1
        # 当前日期对象自增一天，不考虑年
        # 超过当月最大日期，月加1
        if self.day == self.max_day():
            self.add_a_month()
            self.day = 1
        else :
            self.day = self.day+1
        
    def __str__(self):
        stri = str(self.year) + "Y"
        stri = stri + str(self.month) + "M"
        stri = stri + str(self.day) + "D"
        return stri