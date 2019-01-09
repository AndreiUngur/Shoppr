from utils import app, db
from schema import Mutation, Query
from flask_graphql import GraphQLView
import graphene

schema = graphene.Schema(query=Query, mutation=Mutation)

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
    return '<h1>Welcome to my store!</h1>'

if __name__ == '__main__':
     app.run()

