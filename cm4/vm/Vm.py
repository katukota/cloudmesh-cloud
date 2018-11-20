from cm4.vm.Cmaws import Cmaws
from cm4.vm.Cmazure import Cmazure
from cm4.vm.Cmopenstack import Cmopenstack
from cm4.configuration.config import Config
from cm4.cmmongo.mongoDB import MongoDB
from cm4.configuration.name import Name
from cm4.vm.thread import thread
from cm4.configuration.counter import Counter


class Vmprovider (object):

    def __init__(self):
        self.config = Config()

    def get_provider(self, cloud):
        """
        Create the driver based on the 'kind' information.
        This method could deal with AWS, AZURE, and OPENSTACK for CLOUD block of YAML file.
        Only developed for AZURE, AWS, Chameleon, but we haven't test OPENSTACK
        :return: the driver based on the 'kind' information
        """

        os_config = self.config.get('cloud.%s' % cloud)
        if os_config.get('cm').get('kind') == 'azure':
            driver = Cmazure(self.config, cloud).driver
        elif os_config.get('cm').get('kind') == 'aws':
            driver = Cmaws(self.config, cloud).driver
        elif os_config.get('cm').get('kind') == 'openstack':
            driver = Cmopenstack(self.config, cloud).driver
        return driver


class Vm(object):

    def __init__(self, cloud):
        config = Config()
        self.provider = Vmprovider().get_provider(cloud)    # driver
        self.mongo = MongoDB(host=config.get('data.mongo.MONGO_HOST'),
                             username=config.get('data.mongo.MONGO_USERNAME'),
                             password=config.get('data.mongo.MONGO_PASSWORD'),
                             port=config.get('data.mongo.MONGO_PORT'))

    def start(self, name):
        """
        start the node based on the id
        :param name:
        :return: VM document
        """

        info = self.info(name)
        if info.state != 'running':
            self.provider.ex_start_node(info)
            thread(self, 'test', name, 'running').start()
            document = self.mongo.find_document('cloud', 'name', name)
            return document
        else:
            document = self.mongo.find_document('cloud', 'name', name)
            return document

    def stop(self, name):
        """
        stop the node based on the ide
        :param name:
        :return: VM document
        """
        info = self.info(name)
        if info.state != 'stopped':
            self.provider.ex_stop_node(info)
            thread(self, 'test', name, 'stopped').start()
            document = self.mongo.find_document('cloud', 'name', name)
            return document
        else:
            document = self.mongo.find_document('cloud', 'name', name)
            return document

    def resume(self, name):
        """
        start the node based on id
        :param name:
        """
        return self.start(name)

    def suspend(self, name):
        """
        stop the node based on id
        :param name:
        """
        return self.stop(name)

    def destroy(self, name):
        """
        delete the node based on id
        :param name:
        :return: True/False
        """
        result = self.provider.destroy_node(self.info(name))
        self.mongo.delete_document('cloud', 'name', name)
        return result

    '''
    def create(self):
        """
        create a new node
        :param name: the name for the new node
        :return:
        """
        name = self.new_name('test', 'test', 'luoyu')
        node = self.provider.create_node(name=name, **self.provider.get_new_node_setting())
        self.mongo.insert_cloud_document(vars(node))
        return node
    '''

    def list(self):
        """
        list existed nodes
        :return: all nodes' information
        """
        result = self.provider.list_nodes()
        return result

    def status(self, name):
        """
        show node information based on id
        :param name:
        :return: all information about one node
        """
        self.info(name).state
        status = self.mongo.find_document('cloud', 'name', name)['state']
        return status

    def info(self, name):
        """
        show node information based on id
        :param name:
        :return: all information about one node
        """
        nodes = self.list()
        for i in nodes:
            if i.name == name:
                document = vars(i)
                self.mongo.update_document('cloud', 'name', name, document)
                return i

    def new_name(self, experiment, group, user):
        counter = Counter()
        count = counter.get()
        name = Name()
        name_format = {'experiment': experiment, 'group': group, 'user': user, 'counter': count}
        name.set_schema('instance')
        counter.incr()
        counter.set()
        return name.get(name_format)


def process_arguments(arguments):
    """
    Process command line arguments to execute VM actions.
    Called from cm4.command.command
    :param arguments:
    """
    print("vm")
    print(arguments)