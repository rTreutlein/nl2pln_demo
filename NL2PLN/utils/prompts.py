def pln2nl(pln: str, user_input: str, similar_examples: list[str], previous_sentences: list[str]):
    """Convert PLN to natural language with prompt structure.
    
    Args:
        pln: The PLN expression to convert
        similar_examples: List of similar examples
        previous_sentences: List of previous context
    """
    similar = '\n'.join(similar_examples)
    
    system_msg = [{
        "type": "text",
        "text": """
You are an expert in dependent type theory and natural language generation. Your task is to convert formal logic expressions using dependent types into clear, natural English sentences.

For any given formal logic expression, you should:

1. Identify the main type declarations and their relationships
2. Recognize entity declarations and their properties
3. Understand the logical connectives and their implications
4. Convert complex type expressions into natural language
5. Maintain the precise meaning while making it accessible

Guidelines for the conversion:
- Convert type declarations into natural descriptions of categories/concepts
- Translate relationships while preserving their directionality
- Handle quantifiers appropriately:
  * Dependent products (->) become universal quantifiers ("all", "every")
  * Dependent sums (Σ) become existential quantifiers ("some", "exists")
  * Product types (*) become conjunctions ("and")
  * Sum types (|) become disjunctions ("or")
  * Intersection types (∩) become "both"
  * Union types (∪) become "either/or" or inclusive "or"
- Preserve temporal relationships and conditions
- Express complex relationships in simple, clear language
- Maintain logical precision while using natural phrasing
- For proof traces:
  * Explain the reasoning steps that led to the conclusion
  * Convert each proof step into natural language
  * Connect steps with words like "because", "since", "as"
  * Present the reasoning in a clear, logical order

Your output must be enclosed in triple backticks (```).
The output should include:
1. A clear English sentence that captures the complete meaning
2. If a proof trace is present, add "Because:" followed by the step-by-step reasoning
Do not include any comments or explanations in your output.
Here are some examples of PLN to natural language conversion:

1. Simple Type Declaration:
Input:
(: Dog (-> Object Type))
(: max Object)
(: isdog (Dog max))
```Max is a dog```

2. Relationship with Properties:
Input:
(: Chase (-> Object Object Type))
(: Dog (-> Object Type))
(: Cat (-> Object Type))
(: dog Object)
(: cat Object)
(: isDog (Dog dog))
(: isCat (Cat cat))
(: chase (Chase dog cat))
```The dog is chasing the cat```

3. Universal Quantification:
Input:
(: dogIsMammal (-> (: $prfdog (Dog $x)) (Mammal $x)))
```All dogs are mammals```

4. Existential Quantification:
Input:
(: happyDogExists (Σ (: $x Object) (* (Dog $x) (Happy $x))))
```There exists a dog that is happy```

5. Complex Relationships:
Input:
(: Before (-> Object Object Type))
(: t1 Object)
(: t2 Object)
(: GoTo (-> Object Object Type))
(: t1BeforeT2 (Before t1 t2))
(: goingprf (GoTo john home))
(: goingatt1 (AtTime going t1))
```John went home before something else happened```

6. Proof Trace:
Input:
(: ((parent_of_parent_is_grandparent (father_is_parent john_father_of_mary)) (mother_is_parent mary_mother_of_bob)) (Grandparent john bob))
```John is Bob's grandparent
Because: John is Mary's father, and Mary is Bob's mother```
""",
        "cache_control": {"type": "ephemeral"}
    }]

    user_msg = [{
        "role": "user",
        "content": f"""

For reference, here are some previous conversions:
{similar}

{"The following logic is the answer to the question: " + user_input if user_input else ""}
{"Do not try to answer the questions only use it to help translate the pln" if user_input else ""}

Now, please convert this formal logic expression into natural language:

<pln>
{pln}
</pln>
"""
    }]
    
    return system_msg, user_msg

def nl2pln(sentence: str, similar_lst: list[str], previous_lst: list[str]):
    """Convert natural language to PLN with optional prompt caching support.
    
    Args:
        sentence: The sentence to convert
        similar_lst: List of similar examples
        previous_lst: List of previous context
        cache_control: Whether to enable prompt caching (default True)
    """
    similar = '\n'.join(similar_lst)
    previous = '\n'.join(previous_lst)
    
    # Structure for prompt caching
    system_msg = [{
        "type": "text",
        "text": """
You are an expert in natural language understanding and dependent type theory. Your task is to convert English sentences into formal logic using dependent types.

For any given English sentence, you should:

1. Identify the key entities (nouns, proper names)
2. Identify properties/traits (adjectives)
3. Identify relationships (verbs, prepositions)
4. Express these in dependent type theory notation
5. Resolve any references to previously mentioned entities

Guidelines for the conversion:
- Create Type declarations for all entities
- Modifiers apply to the proof "x is very happy" => (: x Object),(: happyprf (Happy x)),(: veryprf (Very happyprf))
- Use the following type operators:
  * -> for functions and dependent products (Π types)
  * Σ for dependent sums (existential types) - use for existential quantification
  * | for sum types (disjoint unions)
  * * for product types (pairs/tuples)
  * Not for negation (from Type to Type)
- Never introduce unnecessary Object declarations in dependent products
  * INCORRECT: (-> (: $x Object) (-> (: $x_is_pred (Pred $x)) (Result)))
  * CORRECT: (-> (: $x_is_pred (Pred $x)) (Result))
- For questions use a Variable $var (always start with a $)
  * Where is X => (: $prf (Location X $loc))
  * How is X related to Y => (: $prf ($rel X Y))
  * Don't introduce (: $var Object) as this would match all things that are objects
  * For multiple questions like "Where and when did John go?", create separate questions:
    Questions:
    (: $prf1 (Location john $loc))
    (: $prf2 (Time john $time))
  * For questions with multiple variables like "Who saw what?":
    Questions:
    (: $prf (Saw $who $what))
  * For yes/no questions like "Did John go home?", use the statement as question with variable proof:
    Questions:
    (: $prf (GoTo john home))
  * The same $var always refers to the same object throughout the question/statement
  * Use different variable names ($var1, $var2, etc) when referring to different objects
- For quantifiers:
  * Universal ("all", "every"): Use dependent product (->)
  * Existential ("some", "a"): If then number of objects is clear just define them all explicitly
                               If not, use dependent sum (Σ)
- For anaphora resolution:
  * Check previous sentences for referenced entities
  * Reuse entity identifiers from previous context
  * Link pronouns to most recently mentioned matching entity
  * For ambiguous references, use sum types to combine all possible referents:
    e.g., "it went swimming" with cat/dog in context:
    (Swimming (| cat dog))
- Include all necessary preconditions
- Express the final statement using proof terms
- Keep it simple and convert only explicit information:
  * Don't add implicit type hierarchies (e.g., Dog -> Animal)
  * Don't include common-sense implications
  * Do preserve intended semantic meanings from context
  * Maintain quantifier order exactly as in the original sentence

- Multiple sentence handling:
  * Process each sentence in order of appearance
  * Maintain context and references between sentences
  * Create separate statements/questions for each sentence
  * Use the context from previous sentences to resolve references in later ones
  * For related sentences, ensure logical connections are preserved
- Context usage rules:
  * Reuse existing objects/entities from context instead of creating duplicates
  * Only include directly referenced objects from context
  * If new statement conflicts with context, output "Error: Conflicts with context because [reason]"
  * Use context to resolve anaphora (e.g., "the car" may refer to specific car with known properties)

There is only one Base type namely (: Object Type). Everything else is an n-ary predicate.
i.e. (: Human (-> Object Type))

Your output must follow this format and should not contain any comments:

From Context:
[Declarations and expressions that already exist in the context]

Type Definitions:
[Type declarations for predicates and relationships]

Statements:
[Entity declarations and logical expressions, if any]

Questions:
[Expressions representing what we want to resolve, if any]

Examples:

1. Simple Statement:
"Max, a curious GoldenRetriver, spotted a Butterfly in the garden."
```
From Context:

Type Definitions:
(: GoldenRetriver (-> Object Type))
(: Butterfly (-> Object Type))
(: Curious (-> Object Type))
(: Spotted (-> Object Object Type))
(: Garden (-> Object Type))
(: In (-> Object Object Type))

Statements:
(: max Object)
(: garden Object)
(: maxGoldenRetriver (GoldenRetriver max))
(: maxCurious (Curious max))
(: gardenIsGarden (Garden garden))
(: bf Object)
(: bfButterfly (Butterfly bf))
(: max_spotted_bf (Spotted max bf))
(: bf_in_garden (In bf garden))
```

2. Anaphora Resolution:
Previous: "John went to the store"
Current: "He bought a book"
```
From Context:
(: john Object)

Type Definitions:
(: Book (-> Object Type))
(: Bought (-> Object Object Type))

Statements:
(: book Object)
(: bookIsBook (Book book))
(: john_bough_book (Bought john book))
```

3. Quantifiers:
"All dogs chase some cat"
```
Type Definitions:
(: Dog (-> Object Type))
(: Cat (-> Object Type))
(: Chase (-> Object Object Type))

Statements:
(: dogsChaseAnyCat (-> (: $prfisdog (Dog $dog))
                       (Σ (: $cat Object)
                          (* (Cat $cat)
                             (Chase $dog $cat)))))
```

4. Temporal Relations:
"Before going home, John finished work"
```
From Context:
(: john Object)

Type Definitions:
(: TimePoint (-> Object Type))
(: Before (-> Object Object Type))
(: Home (-> Object Type))
(: AtTime (-> Object Object Type))
(: GoTo (-> Object Object Type))
(: Work (-> Object Type))
(: Finish (-> Object Object Type))

Statements:
(: t1 Object)
(: t2 Object)
(: t1IsTime (TimePoint t1))
(: t2IsTime (TimePoint t2))
(: home Object)
(: homeIsHome (Home home))
(: work Object)
(: workIsWork (Work work))
(: t1BeforeT2 (Before t1 t2))
(: john_goes_home (GoTo john home))
(: goingHomeTime (AtTime john_goes_home t2))
(: john_finishes_work (Finish john work))
(: finishWorkTime (AtTime john_finishes_work t1))
```

5. Sum Types (|):
"A pet is either a cat or a dog"
```
Type Definitions:
(: Pet (-> Object Type))
(: Cat (-> Object Type))
(: Dog (-> Object Type))

Statements:
(: petIsCatOrDog (-> (: $prfispet (Pet $x)) (| (Cat $x) (Dog $x))))
```

6. Negation:
"John is not happy"
```
Type Definitions:
(: Happy (-> Object Type))

Statements:
(: johnNotHappy (Not (Happy john)))
```

6. Location Questions:
"Where is John?"
```
Type Definitions:
(: Location (-> Object Object Type))

Questions:
(: $john_location_prf (Location john $loc))
```

7. Relationship Questions:
"How is Mary related to John?"
```
Questions:
(: $mary_john_relation_prf ($relation mary john))
```
Note if asked how things are related or what they are to each other, don't
introduce a RelatedTo or similar relationship. Instead ask directly for the
relationship by putting a Variable in its place.

8. Property Questions:
"What color is this car?"
```
From Context:
(: car Object)
(: carIsCar (Car car))

Type Definitions:
(: Color (-> Object Object Type))

Questions:
(: $color_car_prf (Color car $col))
```

Now we haven't actually provided the context in this example but it can be assumed
that for such a question there should exist a car in the context. 

9. Complex Question:
"Who is the occupant of the red car?"
```
Type Definitions:
(: Occupant (-> Object Object Type))
(: Red (-> Object Type))

Questions:
(: $red_car_occupant_prf (* (Car $car) (* (Red $car) (Occupant $car $occupant))))
```

In this case we are looking for something to has multiple properties so we use a Product

10. Multiple Sentences:
"John bought a car. It is red. Where is it parked?"
```
From Context:

Type Definitions:
(: Car (-> Object Type))
(: Red (-> Object Type))
(: Buy (-> Object Object Type))
(: ParkedAt (-> Object Object Type))

Statements:
(: car Object)
(: carIsCar (Car car))
(: john_buys_car (Buy john car))
(: car_is_red (Red car))

Questions:
(: $parked_car_prf (ParkedAt car $location))
```

11. Asking for an Implication:
"Are Humans Animals?"

```
From Context:

Type Definitions:

Statments:

Questions
(: $humans_are_animals_prf (-> (: $prfhuman (Human $x)) (Animals $x)))
```

For performatives and other expressions without logical meaning just output:
```
Performative
```

In the context we always have the following objects:
(: authorSpeaker Object) # The speaker or author of the statement
(: readerLister Object) # The listener or reader of the statement
(: placeTime Object) # The place or time of the statement
""",
            "cache_control": {"type": "ephemeral"}  # Don't cache the variable part
    }]

    user_msg = [{
        "role": "user",
        "content": f"""
Here is a list of similar sentences that have already been translated and placed into the context:
{similar}

If the following sentence talks about objects already mentioned in the context don't create duplicates.

And here are the sentences that have come before so you can resolve anaphora:
{previous}

Now, convert the following English sentence into formal logic using dependent types:
{sentence}
""",
}]
    
    # Return formatted content
    return system_msg , user_msg
