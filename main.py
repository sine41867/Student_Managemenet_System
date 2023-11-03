from flask import Flask, request, redirect, url_for, render_template, session
from flask_bcrypt import Bcrypt 
import pymysql


app = Flask(__name__)
app.static_folder = 'static'
app.secret_key = "sineth"


'''
db_host = "sql8.freesqldatabase.com"
db_user = "sql8656785"
db_password = "Ned1c4sxcD"
db_name = "sql8656785" 
'''
db_host = "Your_Host"
db_user = "Your_Username"
db_password = "Your_Password"
db_name = "Your_Database_Name" 


bcrypt = Bcrypt(app) 

def is_logged_in():
    return 'user_id' in session

def is_profile_set():
    return 'setted_profile' in session and session['setted_profile'] == True

def calculateGPA(student_id):
    try:
        conn = pymysql.connect(host= db_host, user = db_user, password= db_password, database= db_name)
    except:
        return "Can't connect to server"
    
    try:
        
        cursor = conn.cursor()

        query_2 = "SELECT course_id, grade FROM tbl_course_enrollment where student_id = %s"
        cursor.execute(query_2,student_id)
        result_2 = cursor.fetchall()
        if result_2:
            query = "SELECT * FROM tbl_gpa where student_id = %s"
            cursor.execute(query,student_id)
            result = cursor.fetchone()

            if result:
                total_credits = 0.00
                total_value = 0.00
                for row in result_2:
                    course_id = row[0]
                    credit = float(course_id[4])
                    grade = row[1]
             
                    if grade == "A" or grade == "A+":
                        value = 4
                    elif grade == "A-":
                        value = 3.7
                    elif grade == "B+":
                        value = 3.3
                    elif grade == "B":
                        value = 3.0
                    elif grade == "B-":
                        value = 2.7
                    elif grade == "C+":
                        value = 2.3
                    elif grade == "C":
                        value = 2.0
                    elif grade == "C-":
                        value = 1.7
                    elif grade == "D+":
                        value = 1.3
                    elif grade == "D":
                        value = 1.0
                    elif grade == "E":
                        value = 0
                    else:
                        value = -1

                    if not value == -1:
                        total_credits += credit
                        total_value += value*credit
                     
                if not total_credits == 0.00:
                    gpa = total_value/total_credits
                    
                    query_2 = "UPDATE tbl_gpa SET gpa = %s WHERE student_id = %s"
                    cursor.execute(query_2, (gpa,  student_id,))
                    conn.commit()
                return None

            else:
                return "Invalid Student Id"
        else:
            return None

    except Exception as e:
        return "Error " + str(e)
    finally:
        cursor.close()
        conn.close()
        return None 

def is_valid_course_id(course_id):
    valid = False
    if not len(course_id) == 7:  
        return valid
    try:
        x = int(course_id[0])
    except:
        try:
            x = int(course_id[1])
        except:
            try:
                x = int(course_id[2])
            except:
                valid = True

    try:
        x = int(course_id[3])
        y = int(course_id[4])
        z = int(course_id[5])
        w = int(course_id[5])
    except:
        valid = False

    return str(valid)
    

@app.route('/', methods=['GET', 'POST'])
def login():   
    
    alertError = None
    session.pop('user_id', None)
    if request.method == 'POST':
        username = request.form['username']
        passcode = request.form['password']

        hashed_password = bcrypt.generate_password_hash(passcode).decode('utf-8')

        try:
            conn = pymysql.connect(host= db_host, user = db_user, password= db_password, database= db_name)
        except:
            alertError = "Can't connect to server"
            return render_template('login.html', alertError = alertError)
        cursor = conn.cursor()

        try:
            query_1 = "SELECT * FROM tbl_login WHERE username=%s"
            cursor.execute(query_1, (username,))
            result = cursor.fetchone()
            
            query_2 = "SELECT * FROM tbl_users WHERE username=%s"
            cursor.execute(query_2, (username))
            result_2 = cursor.fetchone()
            
            if result:
                is_valid = bcrypt.check_password_hash(result[1],passcode)              
                if  is_valid:
                    session['user_id'] = username
                    session['user_type'] = result[2]
                    if result_2:
                        session['setted_profile'] =True
                        return redirect(url_for('home'))
                    else:
                        session['setted_profile'] = False
                        return redirect(url_for('setup_profile'))
                else:
                    alertError =  "Invalid Password"
            else:
                alertError =  "Invalid Username or Password"
        except Exception as e:
            alertError = str(e)
        finally:
            conn.close()

    return render_template('login.html', alertError = alertError)

@app.route('/admin_home')
def admin_home():
    return render_template("adminHome.html")

@app.route('/student_home')
def student_home():
    return render_template("studentHome.html")
    
@app.route('/management_home')
def management_home():
    return render_template("managementHome.html")

@app.route('/academic_home')
def academic_home():
    return render_template("academicHome.html")

@app.route('/setup_profile',methods=['GET', 'POST'])
def setup_profile():
    alertError = None
    if not is_logged_in():
        return redirect(url_for('login'))

    if is_profile_set():
        return redirect(url_for('home'))

    if request.method == 'POST':
        email = request.form.get('email')
        address = request.form.get('address')
        contact = request.form.get('phone')

        try:
            conn = pymysql.connect(host= db_host, user = db_user, password= db_password, database= db_name)
        except:
            alertError = "Can't connect to server"
            return render_template('setUpProfile.html', alertError = alertError)
        cursor = conn.cursor()
        try:
            query = "INSERT INTO tbl_users (username,type, email, address,contact) VALUES (%s, %s, %s, %s,%s)"
            cursor.execute(query, (session['user_id'], session['user_type'], email, address,contact,))
            conn.commit()
            session['setted_profile'] = True
            return redirect(url_for('home'))
        except:
            alertError = "Error"
        finally:
            cursor.close()
            conn.close()

    return render_template('setUpProfile.html',alertError=alertError)

@app.route('/home')
def home():
    alertError = None
    if not is_logged_in():
        return redirect(url_for('login'))

    if not is_profile_set():
        return redirect(url_for('setup_profile'))

    user_type = session['user_type']

    if user_type == "administrator":
        return redirect(url_for('admin_home'))
    elif user_type == "student":
        return redirect(url_for('student_home'))
    elif user_type == "management":
        return redirect(url_for('management_home'))
    elif user_type == "academic":
        return redirect(url_for('academic_home'))
    else:
        alertError = "Error occurred."
        return render_template('login.html',alertError=alertError)

@app.route('/adminCreateCourse',methods=['GET', 'POST'])
def adminCreateCourse():
    alertError = None
    alertSuccess = None
    if request.method == 'POST':
        course_id = request.form['id']

        if  not is_valid_course_id(course_id):
            alertError = "Invalid Course Id Format"
            return render_template("adminCreateCourse.html",alertError=alertError, alertSuccess = alertSuccess)

        course_name = request.form['name']
        course_description = request.form['description']
        academic_id = request.form['academic']

        try:
            conn = pymysql.connect(host= db_host, user = db_user, password= db_password, database= db_name)
        except:
            alertError = "Can't connect to server"
            return render_template('adminCreateCourse.html', alertError = alertError)
        cursor = conn.cursor()
        try:
            query = "SELECT * FROM tbl_login WHERE username = %s and type = %s"
            cursor.execute(query, (academic_id,"academic"))
            result = cursor.fetchone()
            if result:
                query = "INSERT INTO tbl_courses (course_id, name, description, academic_id) VALUES (%s, %s, %s, %s)"
                cursor.execute(query, (course_id, course_name, course_description, academic_id))
                conn.commit()
                alertSuccess = "Course Created Successfully"
            else:
                alertError = "Invalid Academic Id"
        except:
            alertError = "Course Exist"
        finally:
            cursor.close()
            conn.close()
            return render_template("adminCreateCourse.html",alertError=alertError, alertSuccess = alertSuccess)
    else:
        return render_template("adminCreateCourse.html",alertError=alertError, alertSuccess = alertSuccess)

@app.route('/adminCreateAccounts',methods=['GET', 'POST'])
def adminCreateAccounts():
    alertError = None
    alertSuccess = None
    if request.method == 'POST':
        user_id = request.form['username']
        type = request.form['type']

        hashed_password = bcrypt.generate_password_hash(user_id).decode('utf-8')

        try:
            conn = pymysql.connect(host= db_host, user = db_user, password= db_password, database= db_name)
        except:
            alertError = "Can't connect to server"
            return render_template('adminCreateAccounts.html', alertError = alertError)
        cursor = conn.cursor()
        try:
            query = "INSERT INTO tbl_login (username, password, type) VALUES (%s, %s, %s)"
            cursor.execute(query, (user_id,hashed_password,type,))
            if type == "student":
                query_2 = "INSERT INTO tbl_gpa (student_id, gpa) VALUES (%s, %s)"
                cursor.execute(query_2,(user_id,"0",))
            conn.commit()
            alertSuccess = "Account Created Successfully"
        except Exception as e:
            alertError =  "Account Exist "
        finally:
            cursor.close()
            conn.close()
            return render_template('adminCreateAccounts.html', alertError = alertError,alertSuccess=alertSuccess)
    else: 
        return render_template('adminCreateAccounts.html', alertError = alertError,alertSuccess=alertSuccess)
    
@app.route('/adminAddStudentsToCourse',methods=['GET', 'POST'])
def adminAddStudentsToCourse():
    alertError = None
    alertSuccess = None
    if request.method == 'POST':
        course_id = request.form['id']
        user_id = request.form['username']

        try:
            conn = pymysql.connect(host= db_host, user = db_user, password= db_password, database= db_name)
        except:
            alertError = "Can't connect to server"
            return render_template('adminAddStudentsToCourse.html', alertError = alertError)
        cursor = conn.cursor()

        query_1 = "SELECT * FROM tbl_login WHERE username = %s"
        query_2 = "SELECT * FROM tbl_courses WHERE course_id = %s"

        try:
            cursor.execute(query_1, (user_id,))
            result_1 = cursor.fetchone()

            cursor.execute(query_2, (course_id,))
            result_2 = cursor.fetchone()

            if result_1 and result_2:
                insert_query = "INSERT INTO tbl_course_enrollment (course_id, student_id) VALUES (%s, %s)"
                data = (course_id, user_id)
                cursor.execute(insert_query,data)
                conn.commit()
                alertSuccess = "Enrolled Succussefully"
            else:
                alertError = "Invalid username or course id"
        except:
            alertError =  "Already Enrolled"
        finally:
            cursor.close()
            conn.close()
            return render_template("adminAddStudentsToCourse.html",alertError=alertError, alertSuccess = alertSuccess)
    else: 
        return render_template("adminAddStudentsToCourse.html",alertError=alertError, alertSuccess = alertSuccess)

@app.route('/adminAssignAcademics',methods=['GET', 'POST'])
def adminAssignAcademics():
    alertError = None
    alertSuccess = None
    if request.method == 'POST':
        course_id = request.form['course_id']
        academic_id = request.form['academic']

        try:
            conn = pymysql.connect(host= db_host, user = db_user, password= db_password, database= db_name)
        except:
            alertError = "Can't connect to server"
            return render_template('adminAssignAcademics.html', alertError = alertError)
        cursor = conn.cursor()

        query_1 = "SELECT * FROM tbl_courses WHERE course_id = %s"
        query_2 = "SELECT * FROM tbl_login WHERE username = %s and type ='academic'"

        try:
            cursor.execute(query_1, (course_id,))
            result_1 = cursor.fetchone()

            cursor.execute(query_2, (academic_id,))
            result_2 = cursor.fetchone()

            if result_1 and result_2:
                update_query = "UPDATE tbl_courses SET academic_id = %s WHERE course_id = %s"
                data = (academic_id, course_id)
                cursor.execute(update_query,data)
                conn.commit()
                alertSuccess = "Assigned Successfully"
            else:
                alertError= "Invalid academic id or course id"
        except:
            alertError= "Error Occured"
        finally:
            cursor.close()
            conn.close()
            return render_template("adminAssignAcademics.html",alertError=alertError, alertSuccess = alertSuccess) 
    else:
        return render_template("adminAssignAcademics.html",alertError=alertError, alertSuccess = alertSuccess) 

@app.route('/adminRemoveStudentsFromCourse',methods=['GET', 'POST'])
def adminRemoveStudentsFromCourse():
    alertError = None
    alertSuccess = None
    if request.method == 'POST':
        course_id = request.form['course_id']
        user_id = request.form['username']

        try:
            conn = pymysql.connect(host= db_host, user = db_user, password= db_password, database= db_name)
        except:
            alertError = "Can't connect to server"
            return render_template('adminRemoveStudentsFromCourse.html', alertError = alertError)
        cursor = conn.cursor()

        query = "SELECT * FROM tbl_course_enrollment WHERE course_id = %s AND student_id = %s"
        
        try:
            cursor.execute(query, (course_id,user_id))
            result = cursor.fetchone()

            if result:
                delete_query = "DELETE FROM tbl_course_enrollment WHERE course_id = %s AND student_id = %s"
                data = (course_id, user_id)
                cursor.execute(delete_query,data)
                conn.commit()
                alertError = calculateGPA(user_id)
                
                alertSuccess= "Discarded Successfully"
                
            else:
                alertError= "No records Found"
        except:
            alertError= "Error"
        finally:
            cursor.close()
            conn.close()
            return render_template("adminRemoveStudentsFromCourse.html", alertError = alertError,alertSuccess = alertSuccess)
    else: 
        return render_template("adminRemoveStudentsFromCourse.html", alertError = alertError,alertSuccess = alertSuccess)

@app.route('/adminResetPassword', methods=['GET', 'POST'])
def adminResetPassword():
    alertError = None
    alertSuccess = None
    if request.method == 'POST':
        user_id = request.form['username']

        hashed_password = bcrypt.generate_password_hash(user_id).decode('utf-8')
        
        try:
            conn = pymysql.connect(host= db_host, user = db_user, password= db_password, database= db_name)
        except:
            alertError = "Can't connect to server"
            return render_template('adminResetPassword.html', alertError = alertError)
        cursor = conn.cursor()

        query = "SELECT * FROM tbl_login WHERE username = %s"

        try:
            cursor.execute(query, (user_id,))
            result = cursor.fetchone()

            query2 = "UPDATE tbl_login SET password = %s WHERE username = %s"

            if result:
                cursor.execute(query2, (hashed_password, user_id))
                conn.commit()
                alertSuccess= "Password Resetted Successfully"
            else:
                alertError= "Invalid Username"
        except:
            alertError= "Error"
        finally:
            cursor.close
            conn.close
            return render_template("adminResetPassword.html", alertError = alertError,alertSuccess = alertSuccess)
    else: 
        return render_template("adminResetPassword.html", alertError = alertError,alertSuccess = alertSuccess)

@app.route('/studentRegisterCourse', methods=['GET', 'POST'])
def studentRegisterCourse():
    alertError = None
    alertSuccess = None
    if request.method == 'POST':
        course_id = request.form['id']
        username = session['user_id']

        try:
            conn = pymysql.connect(host= db_host, user = db_user, password= db_password, database= db_name)
        except:
            alertError = "Can't connect to server"
            return render_template('studentRegisterCourse.html', alertError = alertError)
        cursor = conn.cursor()

        query_1 = "SELECT * FROM tbl_courses WHERE course_id = %s"
        query_2 = "SELECT * FROM tbl_course_enrollment WHERE course_id = %s AND student_id = %s"

        try:
            cursor.execute(query_1, (course_id,))
            result_1 = cursor.fetchone()

            cursor.execute(query_2, (course_id,username))
            result_2 = cursor.fetchone()

            if result_1:
                if result_2:
                    return "Already Enrolled"
                else:
                    insert_query = "INSERT INTO tbl_course_enrollment (course_id, student_id) VALUES (%s, %s)"
                    data = (course_id, username)
                    cursor.execute(insert_query,data)
                    conn.commit()
                    alertSuccess= "Enrolled Successfully"
            else:
                alertError= "Invalid course id"
        except:
            alertError= "Error"
        finally:
            cursor.close()
            conn.close()
            return render_template("studentRegisterCourse.html", alertError = alertError,alertSuccess = alertSuccess)
    else: 
        return render_template("studentRegisterCourse.html", alertError = alertError,alertSuccess = alertSuccess)

@app.route('/studentViewCourse')
def studentViewCourse():
    alertError = None    
    username = session['user_id']
    try:
        conn = pymysql.connect(host= db_host, user = db_user, password= db_password, database= db_name)
    except:
        alertError = "Can't connect to server"
        return render_template('studentViewCoursePage.html', alertError = alertError)
    query = "SELECT course_id FROM tbl_course_enrollment WHERE student_id = %s"
    cursor = conn.cursor()
    
    try:
        cursor.execute(query,(username))
        
        data = cursor.fetchall()
        html=""
        if data:
            html = '<html><head><style>table {border-collapse: collapse;width:30%;margin-left: auto;margin-right: auto;} th, td {border: none; padding: 6px;text-align:center;}</style></head><body>'
            html += '<table>'
            
            for row in data:
                html += f'<tr><td>{row[0]}</td></tr>'
            
            html += '</table></body></html>'
        else:
            alertError= 'No records Found'
    except:
        alertError= "Error"
    finally:
        cursor.close()
        conn.close()
        return render_template("studentViewCoursePage.html", alertError = alertError,html=html)
 

@app.route('/studentResult')
def studentResult():
    alertError = None
    username = session['user_id']
    try:
        conn = pymysql.connect(host= db_host, user = db_user, password= db_password, database= db_name)
    except:
        alertError = "Can't connect to server"
        return render_template('studentResultPage.html', alertError = alertError)
    query = "SELECT course_id, grade FROM tbl_course_enrollment WHERE student_id = %s"
    cursor = conn.cursor()
    
    try:
        cursor.execute(query,(username))
        
        data = cursor.fetchall()
        
        html=""
        if data:
            query_2 = "SELECT gpa FROM tbl_gpa WHERE student_id = %s"
            cursor.execute(query_2,(username))
            result = cursor.fetchone()
            gpa = result[0]
            html = '<html><head><style>table {border-collapse: collapse;width:50%;margin-left: auto;margin-right: auto;} th, td {border: 1px solid black; padding: 6px;text-align:center;}</style></head><body>'
            html += f'<h6><b><center>GPA : {gpa}</center></b></h6>'
            html += '<table><tr><th>Course ID</th><th>Grade</th></tr>'
            
            for row in data:
                html += f'<tr><td>{row[0]}</td><td>{row[1]}</td></tr>'
            
            html += '</table></body></html>'
        else:
            alertError= 'No Records Found'
    except:
        alertError= "Error"
    finally:
        cursor.close()
        conn.close()
        return render_template("studentResultPage.html",html=html, alertError = alertError)

@app.route('/academicsViewRegisteredStudents', methods=['GET', 'POST'])
def academicsViewRegisteredStudents():
    alertError = None
    if request.method == "POST":
        course_id = request.form['course_id']

        try:
            conn = pymysql.connect(host= db_host, user = db_user, password= db_password, database= db_name)
        except:
            alertError = "Can't connect to server"
            return render_template('academicsViewRegisteredStudents.html', alertError = alertError)
        query = "SELECT student_id FROM tbl_course_enrollment WHERE course_id= %s"
        cursor = conn.cursor()
        
        try:
            cursor.execute(query,(course_id))
            
            data = cursor.fetchall()
            
            html=""
            if data:
                html = '<html><head><style>table {border-collapse: collapse;width:30%;margin-left: auto;margin-right: auto;} th, td {border: none; padding: 6px;text-align:center;}</style></head><body>'
                html += f'<h5><center><b>{course_id}</b></center></h5>'
                html += '<table>'
                
                for row in data:
                    html += f'<tr><td>{row[0]}</td></tr>'
                
                html += '</table></body></html>'
            else:
                alertError= 'No records'

        except:
            alertError= "Error"
        finally:
            cursor.close()
            conn.close()
            if alertError:
                return render_template("academicsViewRegisteredStudents.html", alertError = alertError)
            else:
                return render_template("academicsViewRegisteredStudentsPage.html", html=html)
    else:
        return render_template("academicsViewRegisteredStudents.html", alertError = alertError)

@app.route('/managementViewRegisteredStudents', methods=['GET', 'POST'])
def managementViewRegisteredStudents():
    alertError=None
    if request.method == "POST":
        course_id = request.form['course_id']
        try:
            conn = pymysql.connect(host= db_host, user = db_user, password= db_password, database= db_name)
        except:
            alertError = "Can't connect to server"
            return render_template('managementViewRegisteredStudents.html', alertError = alertError)
        query = "SELECT student_id FROM tbl_course_enrollment WHERE course_id= %s"
        cursor = conn.cursor()
        try:
            cursor.execute(query,(course_id))
            
            data = cursor.fetchall()
            
            html=""
            if data:
                html = '<html><head><style>table {border-collapse: collapse;width:30%;margin-left: auto;margin-right: auto;} th, td {border: none; padding: 6px;text-align:center;}</style></head><body>'
                html += f'<h5><center><b>{course_id}</b></center></h5>'
                html += '<table>'
                
                for row in data:
                    html += f'<tr><td>{row[0]}</td></tr>'
                
                html += '</table></body></html>'
            else:
                alertError= 'No records'

        except:
            alertError= "Error"
        finally:
            cursor.close()
            conn.close()
            if alertError:
                return render_template("managementViewRegisteredStudents.html", alertError = alertError)
            else:
                return render_template("managementViewRegisteredStudentsPage.html", html=html)
    else:
        return render_template("managementViewRegisteredStudents.html", alertError = alertError)

@app.route('/managementResultSheets', methods=['GET', 'POST'])
def managementResultSheets():
    alertError = None
    if request.method == "POST":
        student_id = request.form['username']
        try:
            conn = pymysql.connect(host= db_host, user = db_user, password= db_password, database= db_name)
        except:
            alertError = "Can't connect to server"
            return render_template('managementResultSheets.html', alertError = alertError)
        query = "SELECT course_id, grade FROM tbl_course_enrollment WHERE student_id = %s"
        cursor = conn.cursor()
        
        try:
            cursor.execute(query,(student_id))
            
            data = cursor.fetchall()
            
            html=""
            if data:
                query_2 = "SELECT gpa FROM tbl_gpa WHERE student_id = %s"
                cursor.execute(query_2,(student_id))
                result = cursor.fetchone()
                gpa = result[0]
                html = '<html><head><style>table {border-collapse: collapse;width:50%;margin-left: auto;margin-right: auto;} th, td {border: 1px solid black; padding: 6px;text-align:center;}</style></head><body>'
                html += f'<h5><center>{student_id}</center></h5>'
                html += f'<h6><b><center>GPA : {gpa}</center></b></h6>'
                html += '<table><tr><th>Course ID</th><th>Grade</th></tr>'
                
                for row in data:
                    html += f'<tr><td>{row[0]}</td><td>{row[1]}</td></tr>'
                
                html += '</table></body></html>'        
            else:
                alertError= 'No records Found'  
        except:
            alertError = "Error"
        
        finally:
            cursor.close()
            conn.close()
            if alertError:
                return render_template("managementResultSheets.html", alertError = alertError)
            else:
                return render_template("managementResultSheetsPage.html", html=html)   
    else:
        return render_template("managementResultSheets.html", alertError = alertError)

@app.route('/managementViewResults', methods=['GET', 'POST'])
def managementViewResults():
    alertError = None
    if request.method == "POST":
        course_id = request.form['course_id']

        try:
            conn = pymysql.connect(host= db_host, user = db_user, password= db_password, database= db_name)
        except:
            alertError = "Can't connect to server"
            return render_template('managementViewResults.html', alertError = alertError)
        query = "SELECT student_id, grade FROM tbl_course_enrollment WHERE course_id= %s"
        cursor = conn.cursor()
        
        try:
            cursor.execute(query,(course_id))
            
            data = cursor.fetchall()
            
            html=""
            if data:
                html = '<html><head><style>table {border-collapse: collapse;width:50%;margin-left: auto;margin-right: auto;}th{text-align:center;} th, td {border: 1px solid black; padding: 6px;}</style></head><body>'
                html += f'<h5><center>{course_id}</center></h5>'
                html += '<table ><tr><th>Student Id</th><th>Grade</th></tr>'
                
                for row in data:
                    html += f'<tr><td>{row[0]}</td><td style="text-align: center;">{row[1]}</td></tr>'
                
                html += '</table></body></html>'
                
            else:
                alertError = 'Invalid Course Id'

        except:
            alertError = "Error"
        finally:
            cursor.close()
            conn.close()
            if alertError:
                return render_template("managementViewResults.html", alertError = alertError)
            else:
                return render_template("managementViewResultsPage.html", html=html)
    else:
        return render_template("managementViewResults.html", alertError = alertError)

@app.route('/managementEnterResults',methods=['GET', 'POST'])
def managementEnterResults():
    alertError = None
    alertSuccess = None
    if request.method == "POST":
        course_id = request.form['course']
        student_id = request.form['student']
        grade = request.form['grade']

        try:
            conn = pymysql.connect(host= db_host, user = db_user, password= db_password, database= db_name)
        except:
            alertError = "Can't connect to server"
            return render_template('managementEnterResults.html', alertError = alertError)
        query_1 = "SELECT * FROM tbl_course_enrollment WHERE course_id = %s AND student_id = %s"
        query_2 = "UPDATE tbl_course_enrollment SET grade = %s WHERE course_id = %s AND student_id = %s"
        cursor = conn.cursor()

        try:
            result_1 = cursor.execute(query_1,(course_id,student_id))

            if result_1:
                cursor.execute(query_2,(grade,course_id,student_id))
                conn.commit()
                alertError = calculateGPA(student_id)
                alertSuccess= "Updated Successfully"
                
                
            else:
                alertError= "Invalid course id or student id"
        except:
            alertError= "Error"
        finally:
            cursor.close()
            conn.close()
            return render_template('managementEnterResults.html', alertError = alertError,alertSuccess = alertSuccess)
    else:
        return render_template('managementEnterResults.html', alertError = alertError,alertSuccess = alertSuccess)
                    
if __name__ == '__main__':
    app.run(debug=True)
