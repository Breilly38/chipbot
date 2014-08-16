## Chipbot

Chipbot is an IRC bot that tracks karma of users.

Chipbot is an offshoot of Bamboo. Original Bamboo source can be found [here](https://github.com/vgmoose/bamboo).

### Debugging

To run Chipbot in debug mode, the following syntax is recommended:
```
python bot.py -n "uniqueusername" -c "#uniquechannel" -d
```

And the bot will join #uniquechannel as uniqueusername on freenode. All messages received will be printed to the terminal.

The ```argparse``` and ```pattern``` modules will also be required, which can be installed via pip:
```
pip install argparse
pip install pattern
```

### Contributing

All pull requests for anything at all are welcome. Chipbot is the product of its creators. To increase the likelihood of your branch being merged, please try to ensure that it is based off master, and GitHub gives it the "ready to merge" status.


### Functionality

#### Ranking

Karma is awarded to users that are presently in the channel. Points can also be awarded to phrases. The differences between the two primarily revolve around the fact that if the object directly to the left of the operator (++/--) is a user, then only the user will be awarded points, whereas phrases can be separated by spaces and the entire word will be awarded points.

Incrementing Karma (User)
- [user]++
- any arbitrary words [user]++

*result: [user] will get +1 karma*

Incrementing Points (Phrase)
- any arbitrary words++

*result: "any arbitrary words" will get +1 point*

Incrementing Karma/Points (Inline)
- any++ arbitrary++ [user]++

*result: "any" will get +1 point*
*result: "arbitrary" will get +1 point*
*result: [user] will get +1 karma*

Checking karma/points rank
- rank [user]
- [user]~~
- ranks

*result: information on the top 5 users and phrases*

#### Channel Stats

Stats are kept track of for each user that sends messages to the channel. That is, every time a user speaks a counter specifically for them is incremented. This keeps track of who is speaking the most in the channel. 

Checking stats
- stats
- stats [user]

*result: information about the top 5 speakers in the channel, or information on specific user*

#### Quality

Quality is calculated by dividing the number of times a user speaks by their rank. This gives a metric for the "quality" of a user's posts (i.e. what percent of them are "good")

Checking quality
- quality
- quality [user]

#### Generosity

Generosity tracks which users are giving the most karma using the ++ commands. Every time a user issues such a command, their generosity value increases. This information will give a metric of who is using the system the most to increase other user's karma.

Checking generosity
- generosity
- generosity [user]

#### Scrambling username

Sometimes it is annoying to be mentioned in the above "leaderboard" style commands. The following command is a workaround that will "scramble" one's username so that they won't be notified in IRC.

- bamboo: scramble

#### Searching

Chipbot is able to search a few different sites, including xkcd, youtube, and bandcamp. It will report the top result, including a link, to the channel. More can be added if requested.

Search youtube
- .yt [search terms]

Search xkcd
- .xkcd [search terms]

Search bandcamp
- .bc [search terms]


