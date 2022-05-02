import importlib
import os
import logging
import time
from py2neo import RelationshipMatcher
from py2neo.ogm import Repository, GraphObject

neo4j_url = os.getenv("PURPLEPANDA_NEO4J_URL")
neo4j_pwd = os.getenv("PURPLEPANDA_PWD")
logger = logging.getLogger(__name__)
repo, graph = None, None

if not neo4j_url:
    print("Error: no env variable PURPLEPANDA_NEO4J_URL witht he neo4j url (e.g.: bolt://neo4j@localhost:7687)")

if not neo4j_pwd:
    print("Error: no env variable PURPLEPANDA_PWD witht he neo4j password")

if neo4j_url and neo4j_pwd:
    repo = Repository(neo4j_url, password=neo4j_pwd)
    graph = repo.graph


class CustomOGM(GraphObject):
    repo = repo

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            if value is not None:
                setattr(self, key, value)
            else:
                setattr(self, key, "") # Change None tpe for empty string to be able to save it in Neo4j

        #db_obj_match = self.__class__.match(self.repo).where(**{self.__primarykey__: getattr(self, self.__primarykey__)})
        db_obj = self.repo.get(self.__class__, getattr(self, self.__primarykey__))
        if db_obj is not None:
            # Update the DB object values with the new ones
            for k in self.__node__.keys():
                if self.__node__[k]:
                    setattr(db_obj, k, self.__node__[k])
            
            for k in db_obj.__node__.keys():
                setattr(self, k, db_obj.__node__[k])
        
            # Update self with the DB object to get the relations and don't overwrite them
            self = db_obj
                    
    def save(self):
        # Always call save from objects before adding relations between them
        start = time.time()
        self.repo.save(self)
        end = time.time()

        # This is for logging purposes
        if hasattr(self, "email") and self.email:
            main_name = self.email
        elif hasattr(self, "name") and self.name:
            main_name = self.name
        else:
            main_name = getattr(self, self.__primarykey__)

        logger.debug(f"Save {self} ({main_name}) took: {int(end - start)}")
        return self 
    
    @classmethod
    def get_all(cls) -> list:
        all_objs = cls.match(repo)
        
        if all_objs.exists():
            return all_objs.all()
        
        logger.warning(f"Objects of class {cls} where searched for but nothing was found")
        return []
    
    @classmethod
    def get_by_email(cls, email: str):
        obj = cls.match(repo).where(email=email).first()
        return obj
    
    @classmethod
    def get_by_name(cls, name: str, or_create=False):
        obj = cls.match(repo).where(name=name).first()
        if not obj and or_create:
            obj = cls(name=name).save()
        return obj
    
    @classmethod
    def get_by_kwargs(cls, *args, **kwargs):
        obj = cls.match(repo).where(*args, **kwargs)
        if obj.exists:
            return obj.first()
        return None
    
    @classmethod
    def get_all_by_kwargs(cls, *args, **kwargs):
        obj = cls.match(repo).where(*args, **kwargs)
        if obj.exists:
            return obj.all()
        return []
    
    @classmethod
    def node_to_obj(cls, node):
        """
        Convert a Py2Neo Node into an object
        """

        labels = str(node.labels).replace(":GcpPrincipal", "").replace(":GcpResource", "")
        if "Gcp" in labels:
            full_module_name = "intel.google.models"
            label_prefixes = ["Gcp", "Google"]
        
        elif "Github" in labels:
            full_module_name = "intel.github.models"
            label_prefixes = ["Github"]
        
        elif "K8s" in labels:
            full_module_name = "intel.k8s.models"
            label_prefixes = ["K8s"]
        
        else:
            full_module_name = "core.models"
            label_prefixes = [""]
        
        class_name = labels.split(":")[-1]
        for l in reversed(labels.split(":")):
            if any(l.startswith(lp) for lp in label_prefixes):
                class_name = l
                break
        
        try:
            models_module = importlib.import_module(full_module_name)
        except Exception as e:
            logger.error(f"Could not find correctly type in labels {labels} ({node}: {e})")
            raise Exception(f"Could not find correctly type in labels {labels} ({node}: {e})")

        klass = getattr(models_module, class_name)
        try:
            obj = klass(**{klass.__primarykey__: node[klass.__primarykey__]}).save()
        except Exception as e:
            logger.error(f"Could not convert correctly to {class_name}, node with labels {labels} ({node}: {e})")
            raise Exception(f"Could not convert correctly to {class_name}, node with labels {labels} ({node}: {e})")
        
        return obj

    
    @classmethod
    def get_all_with_relation(cls, name_rel, where=None, get_only_start=False, get_only_end=False, **kwargs):
        """
        Get all nodes that contains a specific relation
        """

        matcher: RelationshipMatcher = RelationshipMatcher(graph)
        nodes = None

        if where:
            res = matcher.match(nodes, r_type=name_rel, **kwargs).where(where).all()
        else:
            res = matcher.match(nodes, r_type=name_rel, **kwargs).all()
        
        final_nodes = []
        for couple_nodes in res:
            if get_only_start or not get_only_end:
                final_nodes.append(couple_nodes.start_node)
            
            if get_only_end or not get_only_start:
                final_nodes.append(couple_nodes.end_node)
        

        final_objs = [cls.node_to_obj(n) for n in final_nodes]

        # Remove repetitions
        already_checked = set()
        final_uniq_objs = []
        for obj in final_objs:
            pk = getattr(obj, obj.__primarykey__)
            if not pk in already_checked:
                already_checked.add(pk)
                final_uniq_objs.append(obj)

        return final_uniq_objs

    
    def get_by_relation(self, name_rel, where=None, **kwargs):
        """
        name_rel is the name of the relation to search for
        where is a string to run, "_" is the relation object
        kwargs can be used for passing more equal "wheres" to the query in a more safer way
        """

        matcher: RelationshipMatcher = RelationshipMatcher(graph)
        nodes = set([self.__node__]) # Need to be a set to get all directions relationships
        if where:
            res = matcher.match(nodes, r_type=name_rel, **kwargs).where(where).all()
        else:
            res = matcher.match(nodes, r_type=name_rel, **kwargs).all()
        
        # Return only the nodes that aren't the one we are searching from
        final_nodes = []
        for couple_nodes in res:
            if not self.__primaryvalue__ in couple_nodes.start_node.values() and\
                not self.__class__.__name__ in couple_nodes.start_node._labels:
                final_nodes.append(couple_nodes.start_node)
            else:
                final_nodes.append(couple_nodes.end_node)

        # Transform the returned nodes to the expected classes
        final_objs = [self.node_to_obj(n) for n in final_nodes]
        
        return final_objs
    
    def privesc_to(self, rsc, reasons, title, summary, limitations=[]):
        """
        Generate a PRIVESC relationship between the 2 indicated nodes
        self is the origin and "rsc" is the final node
        """

        query = 'MATCH (a:'+self.__primarylabel__+' {'+self.__primarykey__+':"'+self.__primaryvalue__+'"})\n'
        query += 'MATCH (b:'+rsc.__primarylabel__+' {'+rsc.__primarykey__+':"'+rsc.__primaryvalue__+'"})\n'
        query += 'MERGE (a)-[r:PRIVESC {title:"'+title+'", reasons:'+str(reasons)+', summary:"'+summary+'", limitations: "'+limitations+'"}]->(b)\n'
        query += 'RETURN r'
        
        graph.evaluate(query)

        # Return the new object with the new relation
        return self.__class__(**{self.__primarykey__: self.__primaryvalue__}).save()



    
    """def get_by_relation(self, name_rel):
        q = 'MATCH (_:' + cypher_str(self.__class__.__name__) + '{ ' + cypher_str(self.__primarykey__) + ': ' + cypher_repr(self.__primaryvalue__) + '})'
        q += '-[r: ' + cypher_str(name_rel) + ']-() RETURN r'
        results = graph.query(q)
        return [r["r"] for r in results]"""
