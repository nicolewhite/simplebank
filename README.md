# simplebank

## An API for [Simple Bank](https://www.simple.com/)

```python
from simplebank import Simple

simple = Simple('username', 'password')

goals = simple.goals()
transactions = simple.transactions()

goals[0]
transactions[0]

simple.create_goal('Plane Ticket', 750, finish='2016-11-01', color='red')
```
