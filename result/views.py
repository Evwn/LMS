from django.shortcuts import render, get_object_or_404
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse
from django.utils import timezone

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.lib.units import inch
from reportlab.lib import colors

from core.models import Session, Semester
from course.models import Course
from accounts.models import Student
from accounts.decorators import lecturer_required, student_required
from .models import TakenCourse, Result
from analytics.ml_utils import LearnerInsightsGenerator
from analytics.models import StudentPerformance
from analytics.views import update_lecturer_performance

from reportlab.graphics.shapes import Drawing, Line, String
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.graphics.charts.legends import Legend
from reportlab.graphics.charts.textlabels import Label
from reportlab.lib.colors import Color, green, red, blue, black
from reportlab.graphics.widgets.markers import Marker
from reportlab.lib.pagesizes import letter
from reportlab.graphics import renderPDF

CM = 2.54


# ########################################################
# Score Add & Add for
# ########################################################
@login_required
@lecturer_required
def add_score(request):
    """
    Shows a page where a lecturer will select a course allocated
    to him for score entry. in a specific semester and session
    """
    current_session = Session.objects.filter(is_current_session=True).first()
    current_semester = Semester.objects.filter(
        is_current_semester=True, session=current_session
    ).first()

    if not current_session or not current_semester:
        messages.error(request, "No active semester found.")
        return render(request, "result/add_score.html")

    # semester = Course.objects.filter(
    # allocated_course__lecturer__pk=request.user.id,
    # semester=current_semester)
    courses = Course.objects.filter(
        allocated_course__lecturer__pk=request.user.id
    ).filter(semester=current_semester)
    context = {
        "current_session": current_session,
        "current_semester": current_semester,
        "courses": courses,
    }
    return render(request, "result/add_score.html", context)


@login_required
@lecturer_required
def add_score_for(request, pk):
    """Add score for a student"""
    try:
        course = get_object_or_404(Course, pk=pk)
        print(f"Found course: {course.title} (ID: {course.id})")
        
        if request.method == "POST":
            # Get students through TakenCourse
            taken_courses = TakenCourse.objects.filter(course=course)
            students = [tc.student for tc in taken_courses]
            print(f"Found {len(students)} students for course {course.title}")
            
            for student in students:
                midterm = request.POST.get(f"midterm_{student.id}")
                final = request.POST.get(f"final_{student.id}")
                quiz = request.POST.get(f"quiz_{student.id}")
                assignment = request.POST.get(f"assignment_{student.id}")
                attendance = request.POST.get(f"attendance_{student.id}")
                total = request.POST.get(f"total_{student.id}")
                comment = request.POST.get(f"comment_{student.id}")
                
                print(f"Processing scores for student {student.get_full_name()}:")
                print(f"Quiz: {quiz}, Assignment: {assignment}, Attendance: {attendance}, Total: {total}")
                
                # Create or update StudentPerformance record
                from analytics.models import StudentPerformance
                from core.models import Semester
                
                # Get current semester
                current_semester = Semester.objects.filter(is_current_semester=True).first()
                if not current_semester:
                    messages.error(request, "No active semester found.")
                    return redirect('manage_score')
                
                # Calculate performance metrics
                quiz_average = float(quiz) if quiz else 0
                assignment_average = float(assignment) if assignment else 0
                attendance_rate = float(attendance) if attendance else 0
                participation_score = (float(quiz) + float(assignment)) / 2 if quiz and assignment else 0
                overall_grade = float(total) if total else 0
                
                # Create or update StudentPerformance record
                performance, created = StudentPerformance.objects.update_or_create(
                    student=student,
                    course=course,
                    semester=current_semester.semester,
                    academic_year=str(timezone.now().year),
                    defaults={
                        'quiz_average': quiz_average,
                        'assignment_average': assignment_average,
                        'attendance_rate': attendance_rate,
                        'participation_score': participation_score,
                        'overall_grade': overall_grade,
                        'resources_accessed': 0,  # This should be updated based on actual resource access
                        'discussion_participation': 0,  # This should be updated based on actual participation
                    }
                )
                print(f"{'Created' if created else 'Updated'} performance record for {student.get_full_name()}")
                
                # Update lecturer performance
                update_lecturer_performance(
                    lecturer=request.user,
                    course=course,
                    semester=current_semester.semester,
                    academic_year=str(timezone.now().year)
                )
                
                # Update the score in the database
                score = TakenCourse.objects.filter(student=student, course=course).first()
                if score:
                    score.mid_exam = midterm
                    score.final_exam = final
                    score.quiz = quiz
                    score.assignment = assignment
                    score.attendance = attendance
                    score.total = total
                    score.comment = comment
                    score.save()
                    print(f"Updated existing score for {student.get_full_name()}")
                else:
                    TakenCourse.objects.create(
                        student=student,
                        course=course,
                        mid_exam=midterm,
                        final_exam=final,
                        quiz=quiz,
                        assignment=assignment,
                        attendance=attendance,
                        total=total,
                        comment=comment
                    )
                    print(f"Created new score for {student.get_full_name()}")
            
            messages.success(request, "Scores have been added successfully!")
            return redirect('manage_score')
        
        # Get students through TakenCourse for GET request
        taken_courses = TakenCourse.objects.filter(course=course)
        students = [tc.student for tc in taken_courses]
        print(f"Found {len(students)} students for course {course.title}")
        context = {
            'course': course,
            'students': students,
        }
        return render(request, 'result/add_score.html', context)
    except Exception as e:
        print(f"Error in add_score_for: {str(e)}")
        messages.error(request, f"An error occurred: {str(e)}")
        return redirect('manage_score')


# ########################################################


@login_required
@student_required
def grade_result(request):
    student = Student.objects.get(student__pk=request.user.id)
    courses = TakenCourse.objects.filter(student__student__pk=request.user.id).filter(
        course__level=student.level
    )
    # total_credit_in_semester = 0
    results = Result.objects.filter(student__student__pk=request.user.id)

    result_set = set()

    for result in results:
        result_set.add(result.session)

    sorted_result = sorted(result_set)

    total_first_semester_credit = 0
    total_sec_semester_credit = 0
    for i in courses:
        if i.course.semester == "First":
            total_first_semester_credit += int(i.course.credit)
        if i.course.semester == "Second":
            total_sec_semester_credit += int(i.course.credit)

    previousCGPA = 0
    # previousLEVEL = 0
    # calculate_cgpa
    for i in results:
        previousLEVEL = i.level
        try:
            a = Result.objects.get(
                student__student__pk=request.user.id,
                level=previousLEVEL,
                semester="Second",
            )
            previousCGPA = a.cgpa
            break
        except:
            previousCGPA = 0

    context = {
        "courses": courses,
        "results": results,
        "sorted_result": sorted_result,
        "student": student,
        "total_first_semester_credit": total_first_semester_credit,
        "total_sec_semester_credit": total_sec_semester_credit,
        "total_first_and_second_semester_credit": total_first_semester_credit
        + total_sec_semester_credit,
        "previousCGPA": previousCGPA,
    }

    return render(request, "result/grade_results.html", context)


@login_required
@student_required
def assessment_result(request):
    student = Student.objects.get(student__pk=request.user.id)
    courses = TakenCourse.objects.filter(
        student__student__pk=request.user.id, course__level=student.level
    )
    result = Result.objects.filter(student__student__pk=request.user.id)

    context = {
        "courses": courses,
        "result": result,
        "student": student,
    }

    return render(request, "result/assessment_results.html", context)


def create_performance_graph(performances, width=400, height=200):
    """Create a performance trend graph using ReportLab"""
    drawing = Drawing(width, height)
    
    # Create the line chart
    lc = HorizontalLineChart()
    lc.x = 50
    lc.y = 50
    lc.height = 125
    lc.width = 300
    
    # Prepare data
    grades = [float(p.overall_grade) for p in performances]
    lc.data = [grades]
    
    # Style the chart
    lc.strokeColor = blue
    lc.fillColor = blue
    lc.lines[0].strokeColor = blue
    lc.lines[0].strokeWidth = 2
    
    # Configure axes
    lc.categoryAxis.categoryNames = [f"Point {i+1}" for i in range(len(grades))]
    lc.categoryAxis.labels.fontName = 'Helvetica'
    lc.categoryAxis.labels.fontSize = 8
    lc.categoryAxis.labels.angle = 0
    
    lc.valueAxis.valueMin = 0
    lc.valueAxis.valueMax = 100
    lc.valueAxis.valueStep = 20
    lc.valueAxis.labels.fontName = 'Helvetica'
    lc.valueAxis.labels.fontSize = 8
    
    # Add title
    title = String(lc.x + lc.width/2, lc.y + lc.height + 20, 
                  "Performance Trend", 
                  textAnchor='middle',
                  fontSize=10,
                  fontName='Helvetica-Bold')
    drawing.add(title)
    
    # Add the chart to the drawing
    drawing.add(lc)
    
    # Add trend line
    if len(grades) > 1:
        first_grade = grades[0]
        last_grade = grades[-1]
        trend_color = green if last_grade >= first_grade else red
        
        # Add trend line
        trend_line = Line(
            lc.x, lc.y + (lc.height * (first_grade/100)),
            lc.x + lc.width, lc.y + (lc.height * (last_grade/100)),
            strokeColor=trend_color,
            strokeWidth=2
        )
        drawing.add(trend_line)
        
        # Add legend
        legend = Legend()
        legend.alignment = 'right'
        legend.fontName = 'Helvetica'
        legend.fontSize = 8
        legend.colorNamePairs = [
            (blue, 'Actual Performance'),
            (trend_color, 'Trend')
        ]
        legend.x = lc.x + lc.width - 100
        legend.y = lc.y + lc.height + 5
        drawing.add(legend)
    
    return drawing


@login_required
@lecturer_required
def result_sheet_pdf_view(request, id):
    current_semester = Semester.objects.get(is_current_semester=True)
    current_session = Session.objects.get(is_current_session=True)
    result = TakenCourse.objects.filter(course__pk=id)
    course = get_object_or_404(Course, id=id)
    no_of_pass = TakenCourse.objects.filter(course__pk=id, comment="PASS").count()
    no_of_fail = TakenCourse.objects.filter(course__pk=id, comment="FAIL").count()

    # Get ML insights for each student
    insights_generator = LearnerInsightsGenerator()
    student_insights = {}
    
    for student_result in result:
        student = student_result.student
        # Get student performance data
        student_performances = StudentPerformance.objects.filter(
            student=student,
            course=course
        ).order_by('-created_at')
        
        if student_performances.exists():
            latest_performance = student_performances.first()
            historical_performances = list(student_performances[1:6])  # Get last 5 performances
            try:
                ml_insights = insights_generator.generate_insights_report(
                    latest_performance,
                    historical_performances
                )
                student_insights[student.id] = ml_insights
            except Exception as e:
                # If ML insights generation fails, create basic insights
                student_insights[student.id] = {
                    'learning_style': 'Standard',
                    'performance_trend': 'Stable',
                    'recommendations': [
                        {'recommendation': 'Continue current study habits'},
                        {'recommendation': 'Maintain regular attendance'},
                        {'recommendation': 'Complete all assignments on time'}
                    ]
                }
        else:
            # Create performance record if it doesn't exist
            try:
                performance = StudentPerformance.objects.create(
                    student=student,
                    course=course,
                    quiz_average=float(student_result.quiz or 0),
                    assignment_average=float(student_result.assignment or 0),
                    attendance_rate=float(student_result.attendance or 0),
                    participation_score=float(student_result.quiz or 0) * 0.3 + float(student_result.assignment or 0) * 0.3 + float(student_result.attendance or 0) * 0.4,
                    overall_grade=float(student_result.total or 0)
                )
                try:
                    ml_insights = insights_generator.generate_insights_report(
                        performance,
                        []
                    )
                    student_insights[student.id] = ml_insights
                except Exception as e:
                    # If ML insights generation fails, create basic insights
                    student_insights[student.id] = {
                        'learning_style': 'Standard',
                        'performance_trend': 'Stable',
                        'recommendations': [
                            {'recommendation': 'Continue current study habits'},
                            {'recommendation': 'Maintain regular attendance'},
                            {'recommendation': 'Complete all assignments on time'}
                        ]
                    }
            except Exception as e:
                # If performance record creation fails, create basic insights
                student_insights[student.id] = {
                    'learning_style': 'Standard',
                    'performance_trend': 'Stable',
                    'recommendations': [
                        {'recommendation': 'Continue current study habits'},
                        {'recommendation': 'Maintain regular attendance'},
                        {'recommendation': 'Complete all assignments on time'}
                    ]
                }

    fname = (
        str(current_semester)
        + "_semester_"
        + str(current_session)
        + "_"
        + str(course)
        + "_resultSheet.pdf"
    )
    fname = fname.replace("/", "-")
    flocation = settings.MEDIA_ROOT + "/result_sheet/" + fname

    doc = SimpleDocTemplate(
        flocation,
        rightMargin=0,
        leftMargin=6.5 * CM,
        topMargin=0.3 * CM,
        bottomMargin=0,
    )
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(name="ParagraphTitle", fontSize=11, fontName="FreeSansBold")
    )
    Story = [Spacer(1, 0.2)]
    style = styles["Normal"]

    # Add logo
    logo = settings.STATICFILES_DIRS[0] + "/img/brand.png"
    im = Image(logo, 1 * inch, 1 * inch)
    im.__setattr__("_offs_x", -200)
    im.__setattr__("_offs_y", -45)
    Story.append(im)

    # Title
    style = getSampleStyleSheet()
    normal = style["Normal"]
    normal.alignment = TA_CENTER
    normal.fontName = "Helvetica"
    normal.fontSize = 12
    normal.leading = 15
    title = (
        "<b> "
        + str(current_semester)
        + " Semester "
        + str(current_session)
        + " Result Sheet</b>"
    )
    title = Paragraph(title.upper(), normal)
    Story.append(title)
    Story.append(Spacer(1, 0.1 * inch))

    # Course lecturer
    style = getSampleStyleSheet()
    normal = style["Normal"]
    normal.alignment = TA_CENTER
    normal.fontName = "Helvetica"
    normal.fontSize = 10
    normal.leading = 15
    title = "<b>Course lecturer: " + request.user.get_full_name + "</b>"
    title = Paragraph(title.upper(), normal)
    Story.append(title)
    Story.append(Spacer(1, 0.1 * inch))

    # Level
    normal = style["Normal"]
    normal.alignment = TA_CENTER
    normal.fontName = "Helvetica"
    normal.fontSize = 10
    normal.leading = 15
    level = result.filter(course_id=id).first()
    title = "<b>Level: </b>" + str(level.course.level)
    title = Paragraph(title.upper(), normal)
    Story.append(title)
    Story.append(Spacer(1, 0.6 * inch))

    # Results table
    elements = []
    count = 0
    header = [("S/N", "ID NO.", "FULL NAME", "TOTAL", "GRADE", "POINT", "COMMENT")]

    table_header = Table(header, [inch], [0.5 * inch])
    table_header.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.black),
                ("TEXTCOLOR", (1, 0), (-1, -1), colors.white),
                ("TEXTCOLOR", (0, 0), (0, 0), colors.cyan),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BOX", (0, 0), (-1, -1), 1, colors.black),
            ]
        )
    )
    Story.append(table_header)

    for student in result:
        data = [
            (
                count + 1,
                student.student.student.username.upper(),
                Paragraph(
                    student.student.student.get_full_name.capitalize(), styles["Normal"]
                ),
                student.total,
                student.grade,
                student.point,
                student.comment,
            )
        ]
        color = colors.black
        if student.grade == "F":
            color = colors.red
        count += 1

        t_body = Table(data, colWidths=[inch])
        t_body.setStyle(
            TableStyle(
                [
                    ("INNERGRID", (0, 0), (-1, -1), 0.05, colors.black),
                    ("BOX", (0, 0), (-1, -1), 0.1, colors.black),
                ]
            )
        )
        Story.append(t_body)

        # Add ML insights and performance graph for each student
        if student.student.id in student_insights:
            insights = student_insights[student.student.id]
            Story.append(Spacer(1, 0.2 * inch))
            
            # Learning Style
            style = getSampleStyleSheet()
            normal = style["Normal"]
            normal.alignment = TA_LEFT
            normal.fontName = "Helvetica"
            normal.fontSize = 9
            normal.leading = 12
            title = "<b>Learning Style:</b> " + insights['learning_style']
            title = Paragraph(title, normal)
            Story.append(title)
            
            # Performance Trend
            title = "<b>Performance Trend:</b> " + insights['performance_trend']
            title = Paragraph(title, normal)
            Story.append(title)
            
            # Add performance graph
            student_performances = StudentPerformance.objects.filter(
                student=student.student,
                course=course
            ).order_by('created_at')
            
            if student_performances.exists():
                # Create and add the performance graph
                graph = create_performance_graph(student_performances)
                Story.append(Spacer(1, 0.1 * inch))
                # Convert the drawing to a PDF and add it to the story
                from reportlab.platypus import Image as RLImage
                from io import BytesIO
                buffer = BytesIO()
                renderPDF.draw(graph, buffer)
                buffer.seek(0)
                img = RLImage(buffer)
                img.drawHeight = 2*inch
                img.drawWidth = 4*inch
                Story.append(img)
                Story.append(Spacer(1, 0.2 * inch))
            
            # Recommendations
            title = "<b>Recommendations:</b>"
            title = Paragraph(title, normal)
            Story.append(title)
            
            for rec in insights['recommendations']:
                title = "• " + rec['recommendation']
                title = Paragraph(title, normal)
                Story.append(title)
            
            Story.append(Spacer(1, 0.3 * inch))

    Story.append(Spacer(1, 1 * inch))
    style_right = ParagraphStyle(
        name="right", parent=styles["Normal"], alignment=TA_RIGHT
    )
    tbl_data = [
        [
            Paragraph("<b>Date:</b>_____________________________", styles["Normal"]),
            Paragraph("<b>No. of PASS:</b> " + str(no_of_pass), style_right),
        ],
        [
            Paragraph(
                "<b>Siganture / Stamp:</b> _____________________________",
                styles["Normal"],
            ),
            Paragraph("<b>No. of FAIL: </b>" + str(no_of_fail), style_right),
        ],
    ]
    tbl = Table(tbl_data)
    Story.append(tbl)

    doc.build(Story)

    fs = FileSystemStorage(settings.MEDIA_ROOT + "/result_sheet")
    with fs.open(fname) as pdf:
        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = "inline; filename=" + fname + ""
        return response
    return response


@login_required
@student_required
def course_registration_form(request):
    current_session = Session.objects.get(is_current_session=True)
    courses = TakenCourse.objects.filter(student__student__id=request.user.id)
    fname = request.user.username + ".pdf"
    fname = fname.replace("/", "-")
    # flocation = '/tmp/' + fname
    # print(MEDIA_ROOT + "\\" + fname)
    flocation = settings.MEDIA_ROOT + "/registration_form/" + fname
    doc = SimpleDocTemplate(
        flocation, rightMargin=15, leftMargin=15, topMargin=0, bottomMargin=0
    )
    styles = getSampleStyleSheet()

    Story = [Spacer(1, 0.5)]
    Story.append(Spacer(1, 0.4 * inch))
    style = styles["Normal"]

    style = getSampleStyleSheet()
    normal = style["Normal"]
    normal.alignment = TA_CENTER
    normal.fontName = "Helvetica"
    normal.fontSize = 12
    normal.leading = 18
    title = "<b>EZOD UNIVERSITY OF TECHNOLOGY, ADAMA</b>"  # TODO: Make this dynamic
    title = Paragraph(title.upper(), normal)
    Story.append(title)
    style = getSampleStyleSheet()

    school = style["Normal"]
    school.alignment = TA_CENTER
    school.fontName = "Helvetica"
    school.fontSize = 10
    school.leading = 18
    school_title = (
        "<b>SCHOOL OF ELECTRICAL ENGINEERING & COMPUTING</b>"  # TODO: Make this dynamic
    )
    school_title = Paragraph(school_title.upper(), school)
    Story.append(school_title)

    style = getSampleStyleSheet()
    Story.append(Spacer(1, 0.1 * inch))
    department = style["Normal"]
    department.alignment = TA_CENTER
    department.fontName = "Helvetica"
    department.fontSize = 9
    department.leading = 18
    department_title = (
        "<b>DEPARTMENT OF COMPUTER SCIENCE & ENGINEERING</b>"  # TODO: Make this dynamic
    )
    department_title = Paragraph(department_title, department)
    Story.append(department_title)
    Story.append(Spacer(1, 0.3 * inch))

    title = "<b><u>STUDENT COURSE REGISTRATION FORM</u></b>"
    title = Paragraph(title.upper(), normal)
    Story.append(title)
    student = Student.objects.get(student__pk=request.user.id)

    tbl_data = [
        [
            Paragraph(
                "<b>Registration Number : " + request.user.username.upper() + "</b>",
                styles["Normal"],
            )
        ],
        [
            Paragraph(
                "<b>Name : " + request.user.get_full_name.upper() + "</b>",
                styles["Normal"],
            )
        ],
        [
            Paragraph(
                "<b>Session : " + current_session.session.upper() + "</b>",
                styles["Normal"],
            ),
            Paragraph("<b>Level: " + student.level + "</b>", styles["Normal"]),
        ],
    ]
    tbl = Table(tbl_data)
    Story.append(tbl)
    Story.append(Spacer(1, 0.6 * inch))

    style = getSampleStyleSheet()
    semester = style["Normal"]
    semester.alignment = TA_LEFT
    semester.fontName = "Helvetica"
    semester.fontSize = 9
    semester.leading = 18
    semester_title = "<b>FIRST SEMESTER</b>"
    semester_title = Paragraph(semester_title, semester)
    Story.append(semester_title)

    # FIRST SEMESTER
    count = 0
    header = [
        (
            "S/No",
            "Course Code",
            "Course Title",
            "Unit",
            Paragraph("Name, Siganture of course lecturer & Date", style["Normal"]),
        )
    ]
    table_header = Table(header, 1 * [1.4 * inch], 1 * [0.5 * inch])
    table_header.setStyle(
        TableStyle(
            [
                ("ALIGN", (-2, -2), (-2, -2), "CENTER"),
                ("VALIGN", (-2, -2), (-2, -2), "MIDDLE"),
                ("ALIGN", (1, 0), (1, 0), "CENTER"),
                ("VALIGN", (1, 0), (1, 0), "MIDDLE"),
                ("ALIGN", (0, 0), (0, 0), "CENTER"),
                ("VALIGN", (0, 0), (0, 0), "MIDDLE"),
                ("ALIGN", (-4, 0), (-4, 0), "LEFT"),
                ("VALIGN", (-4, 0), (-4, 0), "MIDDLE"),
                ("ALIGN", (-3, 0), (-3, 0), "LEFT"),
                ("VALIGN", (-3, 0), (-3, 0), "MIDDLE"),
                ("TEXTCOLOR", (0, -1), (-1, -1), colors.black),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.black),
                ("BOX", (0, 0), (-1, -1), 0.25, colors.black),
            ]
        )
    )
    Story.append(table_header)

    first_semester_unit = 0
    for course in courses:
        if course.course.semester == settings.FIRST:
            first_semester_unit += int(course.course.credit)
            data = [
                (
                    count + 1,
                    course.course.code.upper(),
                    Paragraph(course.course.title, style["Normal"]),
                    course.course.credit,
                    "",
                )
            ]
            count += 1
            table_body = Table(data, 1 * [1.4 * inch], 1 * [0.3 * inch])
            table_body.setStyle(
                TableStyle(
                    [
                        ("ALIGN", (-2, -2), (-2, -2), "CENTER"),
                        ("ALIGN", (1, 0), (1, 0), "CENTER"),
                        ("ALIGN", (0, 0), (0, 0), "CENTER"),
                        ("ALIGN", (-4, 0), (-4, 0), "LEFT"),
                        ("TEXTCOLOR", (0, -1), (-1, -1), colors.black),
                        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.black),
                        ("BOX", (0, 0), (-1, -1), 0.25, colors.black),
                    ]
                )
            )
            Story.append(table_body)

    style = getSampleStyleSheet()
    semester = style["Normal"]
    semester.alignment = TA_LEFT
    semester.fontName = "Helvetica"
    semester.fontSize = 8
    semester.leading = 18
    semester_title = (
        "<b>Total Second First Credit : " + str(first_semester_unit) + "</b>"
    )
    semester_title = Paragraph(semester_title, semester)
    Story.append(semester_title)

    # FIRST SEMESTER ENDS HERE
    Story.append(Spacer(1, 0.6 * inch))

    style = getSampleStyleSheet()
    semester = style["Normal"]
    semester.alignment = TA_LEFT
    semester.fontName = "Helvetica"
    semester.fontSize = 9
    semester.leading = 18
    semester_title = "<b>SECOND SEMESTER</b>"
    semester_title = Paragraph(semester_title, semester)
    Story.append(semester_title)
    # SECOND SEMESTER
    count = 0
    header = [
        (
            "S/No",
            "Course Code",
            "Course Title",
            "Unit",
            Paragraph(
                "<b>Name, Signature of course lecturer & Date</b>", style["Normal"]
            ),
        )
    ]
    table_header = Table(header, 1 * [1.4 * inch], 1 * [0.5 * inch])
    table_header.setStyle(
        TableStyle(
            [
                ("ALIGN", (-2, -2), (-2, -2), "CENTER"),
                ("VALIGN", (-2, -2), (-2, -2), "MIDDLE"),
                ("ALIGN", (1, 0), (1, 0), "CENTER"),
                ("VALIGN", (1, 0), (1, 0), "MIDDLE"),
                ("ALIGN", (0, 0), (0, 0), "CENTER"),
                ("VALIGN", (0, 0), (0, 0), "MIDDLE"),
                ("ALIGN", (-4, 0), (-4, 0), "LEFT"),
                ("VALIGN", (-4, 0), (-4, 0), "MIDDLE"),
                ("ALIGN", (-3, 0), (-3, 0), "LEFT"),
                ("VALIGN", (-3, 0), (-3, 0), "MIDDLE"),
                ("TEXTCOLOR", (0, -1), (-1, -1), colors.black),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.black),
                ("BOX", (0, 0), (-1, -1), 0.25, colors.black),
            ]
        )
    )
    Story.append(table_header)

    second_semester_unit = 0
    for course in courses:
        if course.course.semester == settings.SECOND:
            second_semester_unit += int(course.course.credit)
            data = [
                (
                    count + 1,
                    course.course.code.upper(),
                    Paragraph(course.course.title, style["Normal"]),
                    course.course.credit,
                    "",
                )
            ]
            # color = colors.black
            count += 1
            table_body = Table(data, 1 * [1.4 * inch], 1 * [0.3 * inch])
            table_body.setStyle(
                TableStyle(
                    [
                        ("ALIGN", (-2, -2), (-2, -2), "CENTER"),
                        ("ALIGN", (1, 0), (1, 0), "CENTER"),
                        ("ALIGN", (0, 0), (0, 0), "CENTER"),
                        ("ALIGN", (-4, 0), (-4, 0), "LEFT"),
                        ("TEXTCOLOR", (0, -1), (-1, -1), colors.black),
                        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.black),
                        ("BOX", (0, 0), (-1, -1), 0.25, colors.black),
                    ]
                )
            )
            Story.append(table_body)

    style = getSampleStyleSheet()
    semester = style["Normal"]
    semester.alignment = TA_LEFT
    semester.fontName = "Helvetica"
    semester.fontSize = 8
    semester.leading = 18
    semester_title = (
        "<b>Total Second Semester Credit : " + str(second_semester_unit) + "</b>"
    )
    semester_title = Paragraph(semester_title, semester)
    Story.append(semester_title)

    Story.append(Spacer(1, 2))
    style = getSampleStyleSheet()
    certification = style["Normal"]
    certification.alignment = TA_JUSTIFY
    certification.fontName = "Helvetica"
    certification.fontSize = 8
    certification.leading = 18
    student = Student.objects.get(student__pk=request.user.id)
    certification_text = (
        "CERTIFICATION OF REGISTRATION: I certify that <b>"
        + str(request.user.get_full_name.upper())
        + "</b>\
    has been duly registered for the <b>"
        + student.level
        + " level </b> of study in the department\
    of COMPUTER SICENCE & ENGINEERING and that the courses and credits \
    registered are as approved by the senate of the University"
    )
    certification_text = Paragraph(certification_text, certification)
    Story.append(certification_text)

    # FIRST SEMESTER ENDS HERE

    logo = settings.STATICFILES_DIRS[0] + "/img/brand.png"
    im_logo = Image(logo, 1 * inch, 1 * inch)
    setattr(im_logo, "_offs_x", -218)
    setattr(im_logo, "_offs_y", 480)
    Story.append(im_logo)

    picture = settings.BASE_DIR + request.user.get_picture()
    im = Image(picture, 1.0 * inch, 1.0 * inch)
    setattr(im, "_offs_x", 218)
    setattr(im, "_offs_y", 550)
    Story.append(im)

    doc.build(Story)
    fs = FileSystemStorage(settings.MEDIA_ROOT + "/registration_form")
    with fs.open(fname) as pdf:
        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = "inline; filename=" + fname + ""
        return response
    return response
