import datetime
from pymongo import MongoClient

'''
无需在mongodb中创建数据库，表和字段，代码运行时，自动创建
可查看：https://blog.csdn.net/qq_37193537/article/details/82388461
'''
class DBManger:
    def __init__(self,futureName):
        '''Create Mongodb Connection'''
        self.__client = MongoClient('mongodb://localhost:27017/')
        #创建数据库FutureDatas可按照更换其他名字
        self.__db = self.__client['FutureDatas']
        # print(self.__db.collection_names())
        #创建表，表名是参数名
        self.__col_KDatas = self.__db[futureName]
        #为集合添加索引
        self.__col_KDatas.create_index([("ActionDay",1),("UpdateTime",1)])

    #添加数据,必须是字典形式，形如{'trader_id': 'xxx', 'trader_name': 'xxxx', 'password': 'xxxx', 'is_active': '1'}
    def add_kdata(self, data):
        print("数据为：",data,type(data))
        self.__col_KDatas.insert_one(data)
        return True

    #查询一个字段的数据
    def get_kdata(self,UpdateTime,_id ='_id'):
        res = self.__col_KDatas.find({},{UpdateTime:1,_id:0})
        return res
    #查询一个或者多个字段的数据
    def get_kdatas(self,*args):
        """
        这里*args：（表示的就是将实参中按照位置传值，多出来的值都给args，
        且以元祖的方式呈现，没有参数为（），一个参数为（x,),多个为（x,y,z)
        :param args:
        :return:
        """
        num = len(args)
        dict1 = {}
        print(num)
        for item in range(num):
            dict1[args[item]]=1
        dict1["_id"] = 0
        print(dict1)
        res = self.__col_KDatas.find({}, dict1)
        return res
    #根据条件（时间）查询数据
    def get_kdatas_by_time(self):

        # res = self.__col_KDatas.find({"ActionDay":"20180827"})
        # res = self.__col_KDatas.find({'ActionDay':{"$gte":"20180823","$lte":"20180830"},"UpdateTime":{"$gte":"09:59:40","$lte":"09:59:56"}},{c}).sort([('ActionDay',1),('UpdateTime',1)])
        query = {}
        query["ActionDay"] = {
            "$gte": "20180827",
            "$lte": "20180830"
        }

        query["UpdateTime"] = {
            "$gte": "09:59:40",
            "$lte": "09:59:56"
        }

        projection = {}
        projection["UpdateTime"] = 1.0
        projection["ActionDay"] = 1.0
        projection['HighestPrice'] =1
        projection['OpenPrice'] = 1
        projection['LowestPrice'] = 1
        projection['ClosePrice'] = 1
        projection['LastPrice'] = 1
        projection["_id"] = 0.0

        sort = [(u"ActionDay", 1), (u"UpdateTime", 1)]

        res = self.__col_KDatas.find(query, projection = projection, sort = sort)

        print((res))
        return res
    #根据管道进行查询。可查看：https://blog.csdn.net/qq_37193537/article/details/82388638
    def get_aggregate(self):
        """
        mongodb中的管道，每一次筛选的数据为下一次使用。
        :return:
        """
        _date={}

        #为了方便查询最大，小值，在project中添加了一列k_data数据，这个数据为group分组使用，（也可以使用$sort按大小进行排序，之后选取第一个值）
        res_H_L = self.__col_KDatas.aggregate([
            {
              "$match":{"ActionDay":{"$gte":"20180823","$lte":"20180830"},"UpdateTime":{"$gte":"09:59:40","$lte":"09:59:56"}}
            },
            {
                "$project":{"UpdateTime":1,"ActionDay":1,"LastPrice":1,"_id":0,'k_data':'divid'}
            },
            {
                "$group":{"_id":"$k_data",'HighPrice':{"$max":"$LastPrice"},"LowPrice":{'$min':"$LastPrice"}}
            }

        ])
        res_Open = self.__col_KDatas.aggregate([
            {
                "$match": {"ActionDay": {"$gte": "20180823", "$lte": "20180830"},
                           "UpdateTime": {"$gte": "09:59:40", "$lte": "09:59:56"}}
            },
            {
                "$project": {"UpdateTime": 1, "ActionDay": 1, "LastPrice": 1, "_id": 0, 'k_data': 'divid'}
            },
            {
                "$sort": {"UpdateTime":1}
            },
            {
                "$limit":1
            }

        ])
        res_Close = self.__col_KDatas.aggregate([
            {
                "$match": {"ActionDay": {"$gte": "20180823", "$lte": "20180830"},
                           "UpdateTime": {"$gte": "09:59:40", "$lte": "09:59:56"}}
            },
            {
                "$project": {"UpdateTime": 1, "ActionDay": 1, "LastPrice": 1, "_id": 0, 'k_data': 'divid'}
            },
            {
                "$sort": {"UpdateTime": -1}
            },
            {
                "$limit": 1
            }

        ])
        """
        管道查询的时候，如果没有查询到数据，结果仍然是：<pymongo.command_cursor.CommandCursor object at 0x02CEDD10>
        但循环的时候，什么都没有执行
        """
        for item in res_H_L:
            _date['HighestPrice'] = item['HighPrice']
            _date['LowestPrice'] = item['LowPrice']
        for item in res_Open:
            _date['OpenPrice'] = item['LastPrice']
        for item in res_Close:
            _date["LastPrice"] = item['LastPrice']
        return _date

    def get_aggregate1(self,time_day,time_now,time_now_n):
        _date={}
        _date["ActionDay"]=time_day
        _date["time_now"]=time_now_n

        res_H_L = self.__col_KDatas.aggregate([
            {
              "$match":{"ActionDay":time_day,"UpdateTime":{"$gte":time_now,"$lte":time_now_n}}
            },
            {
                "$project":{"UpdateTime":1,"ActionDay":1,"LastPrice":1,"_id":0,'k_data':'divid'}
            },
            {
                "$group":{"_id":"$k_data",'HighPrice':{"$max":"$LastPrice"},"LowPrice":{'$min':"$LastPrice"}}
            }

        ])
        res_Open = self.__col_KDatas.aggregate([
            {
                "$match": {"ActionDay": time_day,
                           "UpdateTime": {"$gte":time_now,"$lte":time_now_n}}
            },
            {
                "$project": {"UpdateTime": 1, "ActionDay": 1, "LastPrice": 1, "_id": 0, 'k_data': 'divid'}
            },
            {
                "$sort": {"UpdateTime":1}
            },
            {
                "$limit":1
            }

        ])
        res_Close = self.__col_KDatas.aggregate([
            {
                "$match": {"ActionDay": time_day,
                           "UpdateTime": {"$gte":time_now,"$lte":time_now_n}}
            },
            {
                "$project": {"UpdateTime": 1, "ActionDay": 1, "LastPrice": 1, "_id": 0, 'k_data': 'divid'}
            },
            {
                "$sort": {"UpdateTime": -1}
            },
            {
                "$limit": 1
            }

        ])
        """
        管道查询的时候，如果没有查询到数据，结果仍然是：<pymongo.command_cursor.CommandCursor object at 0x02CEDD10>
        但循环的时候，什么都没有执行
        """
        for item in res_H_L:
            _date['HighestPrice'] = item['HighPrice']
            _date['LowestPrice'] = item['LowPrice']
        for item in res_Open:
            _date['OpenPrice'] = item['LastPrice']
        for item in res_Close:
            _date["LastPrice"] = item['LastPrice']

        return _date

    def get_5_date(self,start_datetime,end_datetime,n):
        #开始日期
        date_str_start = start_datetime
        #结束日期
        date_str_end = end_datetime
        #从某天的0点开始计算
        time_str = "00:00:00"
        #将开始日期和时刻合并，这是为了后面记时间间隔
        date_start = date_str_start + " " + time_str
        #将结束时间和时刻合并，结束时间当做循环的判断依据
        _end = date_str_end + " " + time_str#'20180830 00:00:00格式
        #将字符串转为时间
        date_time = datetime.datetime.strptime(date_start, "%Y%m%d %H:%M:%S")
        #初始值，随便给了一个，但一定要小于结束时间
        run_date_n = "19000101 00:00:00"

        total_data = []
        '''
        思路：在开始和结束时间范围内，通过timedelta函数，相当于形成一个等差数列，0,5,10,15，，这样时间就会间隔n分钟输出
        '''
        while run_date_n<_end:
            date_time_now = date_time.strftime("%Y%m%d %H:%M:%S")  # 20180829 00:05:00格式
            # print(date_time_now)
            #将日期和时间分离，分别获取，方便数据库查找数据
            run_date = date_time_now.split()[0]
            run_time = date_time_now.split()[1]

            date_time = date_time+datetime.timedelta(minutes = int(n))
            run_date_n =date_time.strftime("%Y%m%d %H:%M:%S")
            run_date_n_d = run_date_n.split()[0]
            run_date_n_t = run_date_n.split()[1]
            # print(date_time,type(date_time))
            # print(run_date,run_time,run_date_n_d,run_date_n_t)
            #如果时间到达00:00:00，见结果减少一秒，给数据库传参时，以防出错,因为例如23:55:00<args<00:00:00,不存在，也就是查询不到
            if run_date_n_t =="00:00:00":
                run_date_n_t = '23:59:59'

            res = self.get_aggregate1(run_date,run_time,run_date_n_t)
            # print(res)
            if len(res)>2:#即查询到数据

                total_data.append(res)

        return total_data


if __name__== "__main__":
    data1 = {'AskVolume1': 88, 'AskVolume5': 0, 'BidPrice5': 1.7976931348623157e+308, 'UpperLimitPrice': 2759.0, 'LowestPrice': 2476.5, 'BidVolume5': 0, 'AskPrice4': 1.7976931348623157e+308, 'AskVolume4': 0, 'AskVolume3': 0, 'CurrDelta': 1.7976931348623157e+308, 'OpenInterest': 325016.0, 'AveragePrice': 250306.78677256388, 'PreDelta': 0.0, 'TradingDay': '20180824', 'SettlementPrice': 1.7976931348623157e+308, 'InstrumentID': 'j1901', 'BidVolume4': 0, 'AskPrice5': 1.7976931348623157e+308, 'ActionDay': '20180824', 'LowerLimitPrice': 2351.0, 'ClosePrice': 1.7976931348623157e+308, 'BidVolume2': 0, 'BidPrice3': 1.7976931348623157e+308, 'AskPrice3': 1.7976931348623157e+308, 'BidPrice1': 2509.5, 'ExchangeInstID': 'j1901', 'UpdateTime': '07:54:41', 'ExchangeID': 'DCE', 'HighestPrice': 2525.5, 'UpdateMillisec': 500, 'Turnover': 82445048200.0, 'LastPrice': 2510.0, 'AskPrice2': 1.7976931348623157e+308, 'BidVolume1': 4, 'AskVolume2': 0, 'OpenPrice': 2508.0, 'AskPrice1': 2510.5, 'Volume': 329376, 'BidPrice4': 1.7976931348623157e+308, 'PreClosePrice': 2504.5, 'BidPrice2': 1.7976931348623157e+308, 'PreOpenInterest': 372030.0, 'BidVolume3': 0, 'PreSettlementPrice': 2555.0}
    db1 = DBManger('j1901')
    # print(db1.add_kdata(data1))

    # res = db1.get_kdata('UpdateTime')
    # for each in res:
    #     print(each)

    # res = db1.get_kdatas("UpdateTime","HighestPrice",'ActionDay',"TradingDay")
    # for each in res:
    #     print(each)

    # res = db1.get_kdatas_by_time()
    # for each in res:
    #     print(each)

    #
    # res = db1.get_aggregate1("20180830", '09:40:00', "09:50:00")
    # print(res)

    start_datetime = input('请输入开始时间（形如20180830：')
    end_datetime = input('请输入结束时间（形如20180831')
    n = input("请输入k分钟的k值：")
    #包括开始日期，不含结束日期
    res = db1.get_5_date(start_datetime,end_datetime,n)
    for item in res:
        print(item)
    # print(res)
