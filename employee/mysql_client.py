import pymysql
pymysql.install_as_MySQLdb()
from sqlalchemy import (BigInteger, Column, Date, Float, Integer, String,TIMESTAMP,
                        DateTime, create_engine, exc, Numeric,delete)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import func, desc, and_,between
from sqlalchemy.dialects.mysql import insert
from sqlalchemy import delete,select,join,text
import json
from model import Employees,Salaries,Departments,Dept_manager,Dept_emp,Titles
import os
import datetime
from flask import Flask,request,jsonify
 
host = os.getenv('MYSQL_HOST', 'db')
port = os.getenv('MYSQL_PORT', '3306')  # optional
user = os.getenv('MYSQL_USER', 'pymsql')
password = os.getenv('MYSQL_PASSWORD', 'pymsql123')
database = os.getenv('MYSQL_DB', 'employees')

connectionString = f'mysql+pymysql://{user}:{password}@{host}:{port}/{database}'
Base = declarative_base()
engine = create_engine(connectionString, isolation_level="READ UNCOMMITTED", pool_recycle=3600)
Base.metadata.bind = engine
Base.metadata.create_all(engine)
DBsession = sessionmaker(bind=engine)
session = DBsession()


def convertDate(dt):
    return dt.strftime("%Y-%m-%d")

def recordInJson(records):
    obj_arr=[]
    for row in records:
        employee= {
            'empNo': row.emp_no,
            'birthDate': convertDate(row.birth_date),
            'firstName':row.first_name,
            'lastName': row.last_name,
            'gender':row.gender,
            'hireDate':convertDate(row.hire_date)
        }
        obj_arr.append(employee)
    json_data=json.dumps(obj_arr,indent=4)
    return json_data

def fullRecordInJson(records):
    obj_arr=[]
    for row in records:
        print(row)
        employee= {
            'empNo': row.emp_no,
            'birthDate': convertDate(row.birth_date),
            'firstName':row.first_name,
            'lastName': row.last_name,
            'gender':row.gender,
            'hireDate':convertDate(row.hire_date),
            'salary':row.salary,
            'department':row.dept_no,
            'departmentName':row.dept_name,
            'title':row.title  
        }
        obj_arr.append(employee)
    json_data=json.dumps(obj_arr,indent=4)
    return json_data

def salary(records):
    myObj=[]
    for row in records:
        print(row)
        salary={
            'salary':row.salary,
            'fromDate':convertDate(row.from_date),
            'toDate':convertDate(row.to_date)
        }
        myObj.append(salary)
    json_data=json.dumps(myObj,indent=4)
    return json_data
        

# INSERT EMPLOYEES(POST METHOD)
def insertEmployee(dataToBeInserted):
    try:
        results=session.execute(Employees.__table__.insert(),dataToBeInserted)
        session.commit()
        inserted_id=results.inserted_primary_key[0] if results.inserted_primary_key else None
        # if QUERY_LOGGING:
        #     print('Inserted entry: %s' % str(dataToBeInserted))
        return  { "emp_no": inserted_id}
    except Exception as e:
        print("Could not insert into Employee:%s, Error: %s" % (
            str(dataToBeInserted), str(e)))
        raise
    
    
# GET INFORMATION OF EMPLOYEES(GET METHOD)
def getEmployeeById(empNo,date):
    if date is None:
        query=session.query(Employees).filter(Employees.emp_no == empNo).all()
        return recordInJson(query)
    else:    
        join_stmt=join(Employees,Salaries,Employees.emp_no==Salaries.emp_no )\
            .join(Dept_emp,Employees.emp_no==Dept_emp.emp_no)\
            .join(Titles,Employees.emp_no==Titles.emp_no)\
            .join(Departments,Dept_emp.dept_no==Departments.dept_no)
        stmt=select(Employees,Salaries,Dept_emp,Titles,Departments).select_from(join_stmt)\
        .where(and_((Salaries.emp_no==empNo),between(date,Salaries.from_date,Salaries.to_date)))
        with engine.connect() as conn:
            records=conn.execute(stmt).fetchall()
            return fullRecordInJson(records)    

def getSalary(empNo,date):
    if date is not None:
        stmt=select(Salaries).where(and_((Salaries.emp_no==empNo),between(date,Salaries.from_date,Salaries.to_date)))
    else:
        stmt=select(Salaries).where(Salaries.emp_no==empNo).order_by(desc(Salaries.from_date))
    with engine.connect() as conn:
        records=conn.execute(stmt).fetchall()
        return salary(records)
    
def getEmployee(page,page_size):
    records=session.query(Employees).offset((page - 1) * page_size).limit(page_size).all()
    return recordInJson(records)    

def getEmployeeByName(page,page_size,name):
    stmt1=select(Employees).where(func.concat(Employees.first_name, Employees.last_name).like(f'{name}%')).offset((page - 1) * page_size).limit(page_size)
    with engine.connect() as con:
        records=con.execute(stmt1).fetchall()
    return recordInJson(records)


# put method: to update data in database   
def updateRecordsOfEmployee(empNo,data):
    try:
        jsonObj={}
        if 'birthDate' in data:
            jsonObj["birth_date"] = data['birthDate']   # you're assigning the value from the data['birthDate'] dictionary key to the jsonObj["birth_date"] key. 
        if 'firstName' in data:
            jsonObj['first_name']=data['firstName'],
        if 'lastName' in data:
            jsonObj['last_name']= data['lastName'],
        if 'gender' in data:
            jsonObj['gender']=data['gender'],
        if 'hireDate' in data:
            jsonObj['hire_date']=data['hireDate']   
        stmt = Employees.__table__.update().values(jsonObj).where(Employees.emp_no==empNo)
        session.execute(stmt)
        session.commit()
        return  { "result": "succesfully updated"}
    except Exception as e:
        print("Could not update into Employees table")
        raise
    
# delete method:TO Delete any employee data
def deleteEmployeeData(empNo):
    try:
        stmt = delete(Employees).where(Employees.emp_no == empNo)
        session.execute(stmt)
        session.commit()
        return {"result":"succesfully deleted"}
    except Exception as e:
        print("Could not deleteEmployeesData")
        raise
   

def commitSession():
    session.commit()