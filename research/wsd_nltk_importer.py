from collections import defaultdict
import nltk
from nltk.corpus import semcor
from nltk.corpus import wordnet as wn_corpus
import json
import os.path


def extract_sentences(num_sentences=-1):
    """
    Runs the word sense disambiguation task.
    Parameters:
        num_sentences (int): The number of sentences from the corpus to use in the task. The first n sentences
            from the corpus are used and if n=-1, all sentences from the corpus are used.
    Returns:
        list: sentence_list (list of all sentences or the first n sentences of the corpus), word_sense_dict (dictionary with the possible senses of
            each word in the corpus)
    """
    if num_sentences == -1:
        sentence_list_path = "./sentence_list.json"
        word_sense_dict_path = "./word_sense_dict.json"
    else:
        sentence_list_path = "./sentence_list_"+str(num_sentences)+".json"
        word_sense_dict_path = "./word_sense_dict_"+str(num_sentences)+".json"
    if not (os.path.isfile(sentence_list_path) or os.path.isfile(word_sense_dict_path)):
        # Checking that file exists
        sentence_list = []
        word_sense_dict = defaultdict(set)
        if num_sentences == -1:
            semcor_sents = semcor.tagged_sents(tag="sem")
        else:
            semcor_sents = semcor.tagged_sents(tag="sem")[0:num_sentences]
        for sentence in semcor_sents:
            temp_word_sense_dict = defaultdict(set)
            sentence_word_list = []
            for item in sentence:
                if not isinstance(item, nltk.Tree):
                    continue
                if not isinstance(item.label(), nltk.corpus.reader.wordnet.Lemma):
                    continue
                corpus_word = lemma_to_tuple(item.label())
                sentence_word_list.append(corpus_word)
                temp_word_sense_dict[corpus_word[0]].add(corpus_word)
            if len(temp_word_sense_dict) > 1:
                for word, senses in temp_word_sense_dict.items():
                    word_sense_dict[word] = set(word_sense_dict[word])
                    word_sense_dict[word] |= senses
                    word_sense_dict[word] = list(word_sense_dict[word])
                sentence_list.append(sentence_word_list)
        sent_list_file = open(sentence_list_path, 'w')
        json.dump(sentence_list, sent_list_file)
        sent_list_file.close()
        word_sense_dict_file = open(word_sense_dict_path, 'w')
        # Making word sense list from word sense dict
        word_sense_list = []
        for word in word_sense_dict.keys():
            temp_sense_list = []
            temp_sense_list.append(word)
            temp_val_list = []
            for val in word_sense_dict[word]:
                temp_val_list.append(list(val))
            temp_sense_list.append(temp_val_list)
            word_sense_list.append(temp_sense_list)
        json.dump(word_sense_list, word_sense_dict_file, indent=4)
        word_sense_dict_file.close()
    else:
        # Getting json file containing the sentence list and converting the words stored as strings into tuples
        sentence_list = json.load(open(sentence_list_path))
        for sentence_index in range(len(sentence_list)):
            for word_index in range(len(sentence_list[sentence_index])):
                word = sentence_list[sentence_index][word_index]
                sentence_list[sentence_index][word_index] = tuple(word)
        # Getting json file containing word sense dict and converting words stored (values) as strings into tuples
        word_sense_list = json.load(open(word_sense_dict_path))
        word_sense_dict = defaultdict(set)
        for pair_index in range(len(word_sense_list)):
            key = word_sense_list[pair_index][0]
            vals = word_sense_list[pair_index][1]
            for val in vals:
                word_sense_dict[key].add(tuple(val))
    return sentence_list, word_sense_dict



def get_semantic_relations_dict(sentence_list):
    """
    Note: will have to make more edits to the function before inside_corpus = False is accurate, since entries will need
        to be made for all words that have links to them.
    """
    if len(sentence_list) == 30195:
        sem_rel_path = "./semantic_relations_list.json"
    else:
        sem_rel_path = "./semantic_relations_list_"+str(len(sentence_list))+".json"
    if not os.path.isfile(sem_rel_path):
        semantic_relations_list = []
        # These are all the words in the corpus.
        semcor_words = set(sum(sentence_list, []))
        print(len(sum(sentence_list, [])))
        print(sum(sentence_list, []))
        print(len(semcor_words))
        print(semcor_words)
        counter = 0
        for word in semcor_words:
            counter += 1
            print(str(counter) + " out of " + str(len(semcor_words)))
            syn = wn_corpus.synset(word[1])
            lemma = word[0]
            synonyms = [lemma_to_tuple(synon) for synon in syn.lemmas() if lemma_to_tuple(synon) != word]
            # These are all synsets.
            synset_relations = [syn.hypernyms(), syn.hyponyms(),
                                syn.member_holonyms() + syn.substance_holonyms() + syn.part_holonyms(),
                                syn.member_meronyms() + syn.substance_meronyms() + syn.part_meronyms(),
                                syn.attributes(), syn.entailments(), syn.causes(), syn.also_sees(),
                                syn.verb_groups(), syn.similar_tos()]
            lemma_relations = []
            for relation in range(len(synset_relations)):
                lemma_relations.append([])
                # Getting each of the synsets above in synset_relations.
                for syn in range(len(synset_relations[relation])):
                    # Getting the lemmas in each of the synset_relations synsets.
                    syn_lemmas = synset_relations[relation][syn].lemmas()
                    # Adding each lemma to the list
                    for syn_lemma in syn_lemmas:
                        lemma_tuple = lemma_to_tuple(syn_lemma)
                        if word != lemma_tuple:
                            #lemma_relations[relation].append((lemma, synset_relations[relation][syn]))
                            lemma_relations[relation].append(lemma_tuple)
            word_sem_rel_subdict = create_word_sem_rel_dict(synonyms=synonyms,
                                                            hypernyms=lemma_relations[0],
                                                            hyponyms=lemma_relations[1],
                                                            holonyms=lemma_relations[2],
                                                            meronyms=lemma_relations[3],
                                                            attributes=lemma_relations[4],
                                                            entailments=lemma_relations[5],
                                                            causes=lemma_relations[6],
                                                            also_sees=lemma_relations[7],
                                                            verb_groups=lemma_relations[8],
                                                            similar_tos=lemma_relations[9])
            #semantic_relations_dict[word] = word_sem_rel_subdict
            # Adding pairs of word & the dictionary containing its relations to the big json list (since json doesn't let lists be keys)
            # But we can still keep the word_sem_rel_subdict intact since its keys are strings
            semantic_relations_list.append([word, word_sem_rel_subdict])
        sem_rel_file = open("./semantic_relations_list.json", 'w')
        json.dump(semantic_relations_list, sem_rel_file)
        sem_rel_file.close()
    semantic_relations_list = json.load(open("./semantic_relations_list.json"))
    semantic_relations_dict = {}
    for pair in semantic_relations_list:
        key = tuple(pair[0])
        val_dict = pair[1]
        for val_key in ["synonyms", "hypernyms", "hyponyms", "holonyms", "meronyms", "attributes", "entailments",
                        "causes", "also_sees", "verb_groups", "similar_tos"]:
            list_val_vals = val_dict[val_key]
            tuple_val_vals = []
            for val_val in list_val_vals:
                tuple_val_vals.append(tuple(val_val))
            val_dict[val_key] = tuple_val_vals
        semantic_relations_dict[key] = val_dict
    return semantic_relations_dict


# Helper Functions ----------------------------------------------------------------------------------------------------
def lemma_to_tuple(lemma):
    lemma_word = lemma.name()
    synset_string = lemma.synset().name()
    lemma_tuple = (lemma_word, synset_string)
    return lemma_tuple

def create_word_sem_rel_dict(synonyms, hypernyms, hyponyms, holonyms, meronyms, attributes,
                                   entailments, causes, also_sees, verb_groups, similar_tos):
    """
    Creates an empty semantic relations dictionary with given semantic relations for a word.
    Also converts tuples into lemmastrings for storage in json file.
    """
    sem_rel_dict = {"synonyms": set(synonyms), "hypernyms": set(hypernyms), "hyponyms": set(hyponyms),
                    "holonyms": set(holonyms), "meronyms": set(meronyms), "attributes": set(attributes),
                    "entailments": set(entailments), "causes": set(causes), "also_sees": set(also_sees),
                    "verb_groups": set(verb_groups), "similar_tos": set(similar_tos)}
    for rel in sem_rel_dict.keys():
        vals = sem_rel_dict[rel]
        string_vals = []
        for val in vals:
            #string_vals.append(tuple_to_lemmastring(val))
            string_vals.append(list(val))
        sem_rel_dict[rel] = string_vals
    return sem_rel_dict

# Testing---------------------------------------------------------------------------------------------------------------

#sentence_list, word_sense_dict = extract_sentences(200)
#sem_relations_dict = get_semantic_relations_dict(sentence_list)
#print(sem_relations_dict)
