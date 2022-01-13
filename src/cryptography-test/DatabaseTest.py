from logging import error
import pymysql
 
# 打开数据库连接
db = pymysql.connect(host="localhost", user="root", password="Mysql233.", database="testdb")
 
# 使用 cursor() 方法创建一个游标对象 cursor
cursor = db.cursor()
 
# 使用预处理语句创建表
# sql = """CREATE TABLE EMPLOYEE (
#          FIRST_NAME  CHAR(20) NOT NULL,
#          LAST_NAME  CHAR(20),
#          AGE INT,  
#          SEX CHAR(1),
#          INCOME FLOAT )"""

# SQL 插入语句
# sql = """INSERT INTO EMPLOYEE(FIRST_NAME,
#          LAST_NAME, AGE, SEX, INCOME)
#          VALUES ('Donald', 'Trump', 75, 'M', 10000)"""

# SQL 查询语句
sql = "SELECT * from employee;"

try:
   # 执行sql语句
   cursor.execute(sql)
   # 提交到数据库执行
   # db.commit()
   results = cursor.fetchall()
   print(results)
except:
   # 如果发生错误则回滚
   # db.rollback()
   print("error")
 
# 关闭数据库连接
db.close()