## MongoDB

# Installation
macOS (HomeBrew 🍺)
```
brew tap mongodb/brew
brew install mongodb-community
brew install mongodb-community-shell
```

# Connection
VS Code
```
mongodb+srv://visomopokoa8:<db_password>@cluster0.kjjyow6.mongodb.net/
```

MongoDB Shell
```
mongosh "mongodb+srv://cluster0.kjjyow6.mongodb.net/" --apiVersion 1 --username visomopokoa8
```

Password
```
zyx020701
```

# Usage
Database
```
# Create database
use DATABASE_NAME

# Current database
db

# All databases
show dbs

# Delete database
use DATABASE_NAME
db.dropDatabase()
```

Collection
```
# Create collection
db.createCollection(COLLECTION_NAME, OPTIONS)

# All collections
show collections

# Delete collection
db.COLLECTION_NAME.drop()
```

Document
```
# Insert documents
db.COLLECTION_NAME.insertOne(DOCUMENT, OPTIONS)

DOCUMENT = {
    key_1: value_1, 
    key_2: value_2, 
    ...
}

db.COLLECTION_NAME.insertMany(DOCUMENTS, OPTIONS)

DOCUMENTS = [
    DOCUMENT_1, 
    DOCUMENT_2, 
    ...
]

# Update a document if exist, or create a new one if not
db.COLLECTION_NAME.save(DOCUMENT, OPTIONS)


# Delete documents
db.COLLECTION_NAME.deleteOne(FILTER, OPTIONS)
db.COLLECTION_NAME.deleteMany(FILTER, OPTIONS)
db.COLLECTION_NAME.findOneAndDelete(FILTER, OPTIONS)


# Retrieve documents
db.COLLECTION_NAME.find(QUERY, PROJECTION)
db.COLLECTION_NAME.find().pretty()

db.COLLECTION_NAME.findOne(QUERY, PROJECTION)


# Comparison operator
$gt, $lt, $gte, $lte, $eq, $ne

# Logical operator
$and, $or, $not, $nor

# Regular expression
/^A/  # Start with "A"

# Sort documents
db.COLLECTION_NAME.find().sort(
    {
        KEY: -1  # Descending
    }
)

# Limitation & skipping
db.myCollection.find().skip(5).limit(10)
```