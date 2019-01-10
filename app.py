from flask_graphql import GraphQLView
import graphene
from schema import Mutation, Query

from utils import app, db

schema = graphene.Schema(query=Query, mutation=Mutation)

# Basic GraphQL set-up
app.add_url_rule(
    '/graphql',
    view_func=GraphQLView.as_view(
        'graphql',
        schema=schema,
        graphiql=True
    )
)


@app.route('/')
def index():
    welcome_header = '<h1>Welcome to my store!</h1>'
    advertisement = '<p>To know more about me, please visit <a href="http://andreiungur.github.io/">my personal web page.</a></p>'
    graphql_endpoint = '<p>To use this API, visit the GraphQL end-point: <a href="http://127.0.0.1:5000/graphql">/graphql</a></p>'
    return welcome_header + advertisement + graphql_endpoint


if __name__ == '__main__':
     app.run()

