from presence_analyzer.main import app
from presence_analyzer import views


app.add_url_rule('/', 'index', view_func=views.mainpage)

app.add_url_rule('/api/v1/users', 'users', view_func=views.users_view)
app.add_url_rule(
    '/api/v1/mean_time_weekday/<int:user_id>', 'time_weekday',
    view_func=views.mean_time_weekday_view
)
app.add_url_rule(
    '/api/v1/presence_weekday/<int:user_id>', 'presence_weekday',
    view_func=views.presence_weekday_view
)
app.add_url_rule(
    '/api/v1/presence_from_to/<int:user_id>', 'presence_from_to',
    view_func=views.presence_from_to_view
)
app.add_url_rule(
    '/render/<template>', 'render',
    view_func=views.render_page_user
)
