from flask import Flask, request, abort, jsonify
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10


def paginate_questions(request, selection):
    page = request.args.get("page", 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [question.format() for question in selection]
    current_questions = questions[start:end]

    return current_questions


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)

    CORS(app, resources={r"/*": {"origins": "*"}})

    @app.after_request
    def after_request(response):
        response.headers.add(
            "Access-Control-Allow-Headers", "Content-Type,Authorization"
        )
        response.headers.add(
            "Access-Control-Allow-Methods", "GET,PUT,POST,PATCH,DELETE,OPTIONS"
        )
        response.headers.add(
            "Access-Control-Allow-Credentials", "true"
        )

        return response

    @app.route('/categories')
    def categories():
        all_categories = Category.query.all()
        all_categories = {category.id: category.type for
                          category in all_categories}

        return jsonify(
            {"success": True,
             "categories": all_categories}
        )

    @app.route("/questions")
    def retrieve_questions():
        selection = Question.query.all()
        current_questions = paginate_questions(request, selection)
        current_category = Category.query.get(1)
        current_category = current_category.format()["type"]
        question_categories = Category.query.all()
        question_categories = {category.id: category.type for
                               category in question_categories}

        if len(current_questions) == 0:
            abort(404)

        return jsonify(
            {
                "success": True,
                "questions": current_questions,
                "total_questions": len(selection),
                "categories": question_categories,
                "current_category": current_category
            }
        )

    @app.route("/questions/<question_id>", methods=['DELETE'])
    def delete_question(question_id):
        question = Question.query.get(question_id)
        if question:
            try:
                question.delete()
            except:
                abort(500)
            else:
                return jsonify({
                    "success": True
                }), 200
        else:
            abort(422)

    @app.route("/questions", methods=["POST"])
    def add_questions():
        data = request.get_json()
        for i in data.values():
            if i == "":
                abort(422)
        question = data.get('question', None)
        answer = data.get('answer', None)
        difficulty = data.get('difficulty', None)
        category = data.get('category', None)
        new_question = Question(
            question=question,
            answer=answer,
            category=category,
            difficulty=difficulty
        )
        try:
            new_question.insert()
        except Exception as e:
            print(e)
            abort(500)

        return jsonify({
            "success": True
        }), 200

    @app.route("/question", methods=["POST"])
    def search_questions():
        data = request.get_json()

        search_term = data.get("searchTerm", None)

        search_result = Question.query.filter(
            Question.question.ilike(f"%{search_term}%")
        ).all()
        current_search = paginate_questions(request, search_result)
        current_category = Category.query.get(1)
        current_category = current_category.format()["type"]

        return jsonify({
            "success": True,
            "questions": current_search,
            "total_questions": len(search_result),
            "current_category": current_category
        })

    @app.route("/categories/<cat_id>/questions")
    def questions_by_categories(cat_id):
        current_category = Category.query.get(cat_id)
        if current_category:
            current_category = current_category.format()["type"]
            questions = Question.query.filter_by(category=cat_id).all()
            current_questions = paginate_questions(request, questions)

            return jsonify({
                "questions": current_questions,
                "total_questions": len(questions),
                "current_category": current_category,
                "success": True
            })
        else:
            abort(404)

    @app.route("/quizzes", methods=["POST"])
    def get_quiz():
        data = request.get_json()
        previous_question = data.get("previous_questions")
        quiz_category = data.get("quiz_category")
        print(previous_question, quiz_category)

        if quiz_category["id"] == 0:
            all_questions = Question.query.all()
        else:
            all_questions = Question.query.filter_by(
                category=quiz_category["id"])

        question_list = [q.format() for q in all_questions
                         if q.id not in previous_question]
        try:
            question = random.choice(question_list)
        except IndexError:
            abort(404)
        else:

            return jsonify({
                "success": True,
                "question": question
            })

    # error handlers
    @app.errorhandler(404)
    def not_found(error):
        return (
            jsonify({"success": False, "error": 404,
                     "message": "resource not found"}),
            404,
        )

    @app.errorhandler(422)
    def unprocessable(error):
        return (
            jsonify({"success": False, "error": 422,
                     "message": "unprocessable"}),
            422,
        )

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({"success": False, "error": 400,
                        "message": "bad request"}), 400

    @app.errorhandler(500)
    def internal_error(error):
        return (
            jsonify({"success": False, "error": 500,
                     "message": "internal server error"}),
            500,
        )

    return app
