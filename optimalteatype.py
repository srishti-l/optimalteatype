# import statements
import json
import csv
import networkx as nx
import matplotlib.pyplot as plt


class MyGraph:
    """
    A class that manages creating a graph to recommend teas based on health concerns,
    visualizing connections between health benefits, teas, and their characteristics.

    Attributes:
        G (networkx.Graph): The graph object that represents the network of tea-related data.
    """

    def __init__(self):
        """
        Initializes an empty graph.
        """
        self.G = nx.Graph()

    def recommend_tea_for_health(self, health_concern, max_results=5):
        """
        Recommends teas for a given health concern based on the shortest path in the graph.

        Args:
            health_concern (str): The health concern for which to recommend teas.
            max_results (int): The maximum number of tea recommendations to return. Default is 5.

        Returns:
            List[str]: A list of tea names recommended for the given health concern.
        """
        health_node = self.find_closest_node(health_concern)

        if not health_node or self.G.nodes[health_node].get("type") != "health":
            print(f"No matching health concern found for '{health_concern}'.")
            return []
        
        recommended_teas = []
        for node in self.G.nodes:
            if self.G.nodes[node].get("type") == "tea":
                try:
                    path = nx.shortest_path(self.G, source=health_node, target=node)
                    recommended_teas.append((node, path))
                except nx.NetworkXNoPath:
                    continue

        recommended_teas.sort(key=lambda x: len(x[1]))

        if not recommended_teas:
            print(f"No teas found connected to '{health_concern}'.")
        else:
            print(f"Recommended teas for '{health_concern}':")
            for tea, path in recommended_teas[:max_results]:
                print(f"{tea.title()} (Path: {' ➝ '.join(path)})")

        return [tea for tea, _ in recommended_teas[:max_results]]

    def build_graph(self, data, benefit_data):
        """
        Builds a graph based on the provided tea and health benefit data 

        Args:
            data (dict): A dictionary containing different tea types, categories, and associated health benefits 
            benefit_data (list[dict]): A list of dictionaries containing the tea-benefit relationships 

        Returns:
            None
        """
        for category, info in data.items():
            if isinstance(info, dict) and "types" in info:
                category_name = category.strip().lower()
                self.G.add_node(category_name, type="category")
                for tea_key, tea_data in info["types"].items():
                    tea_name = tea_data.get("name", tea_key).strip().lower()
                    self.G.add_node(
                        tea_name,
                        type="tea",
                        caffeine=tea_data.get("caffeine", "N/A"),
                        origin=tea_data.get("origin", "Unknown"),
                        taste=tea_data.get("tasteDescription", "N/A"),
                    )
                    self.G.add_edge(category_name, tea_name)

                    taste = tea_data.get("tasteDescription")
                    if taste:
                        for flavor in [f.strip() for f in taste.split(",")]:
                            self.G.add_node(flavor, type="taste")
                            self.G.add_edge(tea_name, flavor)

                    for benefit in tea_data.get("healthBenefits", []):
                        benefit = benefit.strip().lower()
                        self.G.add_node(benefit, type="health")
                        self.G.add_edge(tea_name, benefit)

        for row in benefit_data:
            teas = [t.strip().lower() for t in row["Tea Type"].split(",")]
            benefits = [b.strip().lower() for b in row["Health Benefit"].split(",")]

            for tea in teas:
                self.G.add_node(tea, type="tea")
                for benefit in benefits:
                    self.G.add_node(benefit, type="health")
                    self.G.add_edge(tea, benefit)

    def find_closest_node(self, keyword):
        """
        Finds the closest matching node in the graph based on a keyword

        Args:
            keyword (str): The keyword to search for in the graph nodes

        Returns:
            str or None: The closest matching node, None if no match is found
        """
        keyword = keyword.lower()
        for node in self.G.nodes:
            if keyword == node.lower():
                return node
        for node in self.G.nodes:
            if keyword in node.lower():
                return node
        return None

    def find_closest_tea_node(self, tea_name):
        """
        Finds the closest tea node that matches the given tea name

        Args:
            tea_name (str): The name of the tea to search for

        Returns:
            str or None: The closest matching tea node, or None if no match is found
        """
        tea_name_lower = tea_name.lower()
        matches = [
            node
            for node in self.G.nodes
            if tea_name_lower in node
            and self.G.nodes[node].get("type") in ["tea", "category"]
        ]
        return matches[0] if matches else None

    def find_shortest_paths(self, health_concern, tea_options):
        """
        Finds and prints the shortest paths between a health concern and a list of tea options.

        Args:
            health_concern (str): The health concern to search for
            tea_options (list[str]): A list of tea names to find paths for

        Returns:
            None
        """
        print(f"\nFinding teas for: {health_concern}")

        health_concern_node = self.find_closest_node(health_concern)
        if not health_concern_node:
            print(f"Health concern '{health_concern}' not found in the graph.")
            return

        for tea in tea_options:
            tea_node = self.find_closest_tea_node(tea)
            tea_nodes = []

            if tea_node and self.G.nodes[tea_node].get("type") == "category":
                tea_nodes = self.get_teas_from_category(tea_node)
                if not tea_nodes:
                    print(f"No teas found in category '{tea_node}'")
                    continue
            else:
                tea_nodes = [tea_node]

            found_path = False
            for actual_tea in tea_nodes:
                if actual_tea not in self.G:
                    continue
                try:
                    path = nx.shortest_path(self.G, source=health_concern_node, target=actual_tea)
                    print(f"Shortest path from '{health_concern}' to '{actual_tea}': {path}")
                    found_path = True
                except nx.NetworkXNoPath:
                    continue

            if not found_path:
                print(f"No path between '{health_concern}' and '{tea}'")

    def get_teas_from_category(self, category_name):
        """
        Returns a list of teas from a specified category.

        Args:
            category_name (str): The name of the tea category.

        Returns:
            list[str]: A list of tea names in the specified category.
        """
        category_node = self.find_closest_node(category_name)
        if category_node and self.G.nodes[category_node]["type"] == "category":
       
            return [
                n
                for n in self.G.neighbors(category_node)
                if self.G.nodes[n].get("type") == "tea"
            ]
        return []

    def explore_tea_by_characteristic(self, keyword):
        """
        Explores teas based on a given characteristic ->(taste, origin, caffeine, health)

        Args:
            keyword (str): The searched characteristic 

        Returns:
            list[str]: A list of tea names associated with the given characteristic 
        """
        keyword = keyword.lower()
        matches = []

        for node in self.G.nodes:
            node_type = self.G.nodes[node].get("type")
            if keyword in node.lower() and node_type in [
                "taste",
                "origin",
                "caffeine",
                "health",
            ]:
                teas = [
                    tea
                    for tea in self.G.neighbors(node)
                    if self.G.nodes[tea].get("type") == "tea"
                ]
                if teas:
                    matches.append((node, teas))

        if not matches:
            print(f"No teas found matching the characteristic '{keyword}'.")
            return None

        recommended_teas = []
        for characteristic, teas in matches:
            for tea in teas:
                recommended_teas.append(tea)

        return recommended_teas

    def list_all_teas(self):
        """
        Prints a list of all available teas in the graph

        Returns:
            None
        """
        print("\nAll Available Teas:")
        for node in self.G.nodes:
            if self.G.nodes[node].get("type") == "tea":
                print(f"{node.title()}")


    def compare_teas(self, tea1, tea2, attribute):
        """
        Compares two teas based on a specified attributes or characteristics of tea

        Args:
            tea1 (str): The name of the first tea
            tea2 (str): The name of the second tea
            attribute (str): The comparison criteria 

        Returns:
            tuple: A tuple containing the values of the characteristic for both teas
        """
        tea1_node = self.find_closest_tea_node(tea1)
        tea2_node = self.find_closest_tea_node(tea2)

        if not tea1_node or not tea2_node:
            print("Could not find both tea types in the graph.")
            return

        value1 = self.get_attribute(tea1_node, attribute)
        value2 = self.get_attribute(tea2_node, attribute)

        if value1 == "N/A" or value2 == "N/A":
            print("One or both teas do not have caffeine information.")
            return

        print(f"\nComparison based on '{attribute.title()}':")
        print(f"{tea1.title()}: {value1}")
        print(f"{tea2.title()}: {value2}")

        return (value1, value2)
    
    def get_attribute(self, tea_node, attribute):
        """
        Retrieves a specific attribute for a given tea node

        Args:
            tea_node (str): The name of the tea node
            attribute (str): The attribute to retrieve

        Returns:
            str: The value of the attribute, or an error message if not found
        """
        if tea_node not in self.G:
            return "Node not found"
        
        node_data = self.G.nodes[tea_node]
        return node_data.get(attribute, "Attribute not found")

    def find_teas(self, health_concerns, taste_preference=None):
        """
        Finds teas that match a list of health concerns, and optionally a taste preference.

        Args:
            health_concerns (list[str]): A list of health concerns to search for.
            taste_preference (str, optional): A taste preference to filter the results.

        Returns:
            list[str]: A list of tea names that match the health concerns and taste preference.
        """

        tea_sets = []
        for concern in health_concerns:
            concern_node = self.find_closest_node(concern)
            if concern_node and self.G.nodes[concern_node].get("type") == "health":
                connected_teas = {
                    tea
                    for tea in self.G.neighbors(concern_node)
                    if self.G.nodes[tea].get("type") == "tea"
                }
                tea_sets.append(connected_teas)

        if not tea_sets:
            print(f"No teas found for any of: {health_concerns}")
            return []

        common_teas = set.intersection(*tea_sets)
        if not common_teas:
            print(f"No teas found that help with all of: {health_concerns}")
            return []

        if taste_preference:
            matching_teas = []
            for tea in common_teas:
                taste = self.G.nodes[tea].get("taste", "").lower()
                if taste_preference.lower() in taste:
                    matching_teas.append(tea)

            if matching_teas:
                print(f"Teas for {health_concerns} with taste '{taste_preference}':")
                for t in matching_teas:
                    print(f"{t.title()}")
                return matching_teas
            else:
                print(
                    f"Teas for {health_concerns}, but no exact taste match for '{taste_preference}':"
                )
                for t in common_teas:
                    print(f"{t.title()}")
                return list(common_teas)

        print(f"Teas matching all health concerns {health_concerns}:")
        for t in common_teas:
            print(f"{t.title()}")
        return list(common_teas)


    def visualize_graph(self, focus_nodes=None):
        """
        Visualizes the full tea network graph, with optional focus on specific nodes 

        Args:
            focus_nodes (list[str]: A list of nodes to highlight in the visualization

        Returns:
            None
        """
        plt.figure(figsize=(15, 10))

        pos = nx.spring_layout(self.G, k=0.5)

        if focus_nodes:
            sub_nodes = set()
            for node in focus_nodes:
                if node in self.G:
                    sub_nodes.add(node)
                    sub_nodes.update(self.G.neighbors(node))
            H = self.G.subgraph(sub_nodes)
        else:
            H = self.G

        color_map = []
        for node in H:
            node_type = self.G.nodes[node].get("type", "unknown")
            if node_type == "tea":
                color_map.append("lightgreen")
            elif node_type == "health":
                color_map.append("lightcoral")
            elif node_type == "taste":
                color_map.append("lightblue")
            elif node_type == "category":
                color_map.append("khaki")
            else:
                color_map.append("grey")

        nx.draw(
            H,
            pos,
            with_labels=True,
            node_color=color_map,
            edge_color="gray",
            node_size=800,
            font_size=8,
        )
        plt.title("Tea Health Network", fontsize=18)
        plt.show()

    def visualize_shortest_path(self, health_concern, tea_target):
        """
        Visualizes the shortest path between a health concern and a tea in the graph

        Args:
            health_concern (str): The health concern to start from
            tea_target (str): The target tea to find the path to

        Returns:
            None
        """
        try:
            path = nx.shortest_path(self.G, source=health_concern, target=tea_target)
            print(f'Shortest path from {health_concern} to {tea_target}: {path}')

            pos = nx.spring_layout(self.G, seed=42)  #

            plt.figure(figsize=(12, 8))

            nx.draw(self.G, pos, node_color='lightgray', edge_color='lightgray', with_labels=True, node_size=2000, font_size=10)

            path_edges = list(zip(path[:-1], path[1:]))  
            nx.draw_networkx_nodes(self.G, pos, nodelist=path, node_color='orange', node_size=3000)
            nx.draw_networkx_edges(self.G, pos, edgelist=path_edges, edge_color='orange', width=3)
            nx.draw_networkx_labels(self.G, pos, font_size=12, font_weight='bold')

            plt.title(f"Shortest Path from '{health_concern}' to '{tea_target}'")
            plt.show()

        except nx.NetworkXNoPath:
            print(f"Sorry, there is no path from {health_concern} to {tea_target}.")
        except nx.NodeNotFound as e:
            print(f"Node not found: {e}")

    def visualize_shortest_path_between_teas(self, tea1, tea2):
        """
        Visualizes the shortest path between two teas in the graph.

        Args:
            tea1 (str): The first tea
            tea2 (str): The second tea

        Returns:
            None
        """
        try:
            path = nx.shortest_path(self.G, source=tea1, target=tea2)
            print(f'Shortest path from {tea1} to {tea2}: {path}')

            sub_nodes = set(path)
            for node in path:
                sub_nodes.update(self.G.neighbors(node))
            H = self.G.subgraph(sub_nodes)

            pos = nx.spring_layout(H, k=0.8)
            plt.figure(figsize=(12, 8))

            node_colors = []
            for node in H:
                if node == tea1:
                    node_colors.append('green')  
                elif node == tea2:
                    node_colors.append('red')    
                elif node in path:
                    node_colors.append('orange')
                else:
                    node_colors.append('lightgray') 

            nx.draw(H, pos, with_labels=True, node_color=node_colors, edge_color='lightgray',
                    node_size=800, font_size=8)

            path_edges = list(zip(path, path[1:]))
            nx.draw_networkx_edges(H, pos, edgelist=path_edges, edge_color='orange', width=3)

            plt.title(f"Shortest Path Between '{tea1}' and '{tea2}'")
            plt.show()

        except nx.NetworkXNoPath:
            print(f"Sorry, there is no path from {tea1} to {tea2}.")
        except nx.NodeNotFound as e:
            print(f"Node not found: {e}")


class TeaBenefits:
    """
    A class to handle loading and processing of tea benefit data from tea benefits CSV

    Attributes:
        benefits_data (list[dict]): A list of dictionaries containing tea-benefit relationships
    """
    def __init__(self):
        """
        Initializes empty list to store tea benefit data.
        """
        self.benefits_data = []

    def readFile(self, file):
        """
        Reads the tea benefit data from a CSV file

        Args:
            file (str): The path to the CSV file containing tea benefit data

        Returns:
            None
        """
        with open(file, newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                self.benefits_data.append(row)

    def printData(self):
        """
        Prints the tea benefit data.

        Returns:
            None
        """
        for entry in self.benefits_data:
            print(f"{entry['Tea Type']} helps with {entry['Health Benefit']}")


class TeaTypes:
    """
    A class to handle loading and processing of tea type data from JSON file

    Attributes:
        tea_data (dict): A dictionary containing tea type information
    """
    def __init__(self):
        """
        Initializes an empty dictionary to store tea type data
        """
        self.tea_data = {}

    def readFile(self, file):
        """
        Reads the tea type data from  JSON file

        Args:
            file (str): The path to the JSON file containing tea type data

        Returns:
            None
        """
        with open(file, "r", encoding="utf-8") as f:
            self.tea_data = json.load(f)

    def printData(self):
        """
        Prints the tea type data.

        Returns:
            None
        """
        for category, info in self.tea_data.items():
            print(f"\nCategory: {category}")
            if "types" in info:
                for tea_name, tea_info in info["types"].items():
                    print()
                    print(f"Tea: {tea_name}")
                    print(f"Origin: {tea_info.get('origin', 'Unknown')}")
                    print(f"Taste: {tea_info.get('tasteDescription', 'N/A')}")
                    print(f"Caffeine: {tea_info.get('caffeine', 'N/A')}")
            else:
                for key, value in info.items():
                    try:
                        print(
                            f"\nTea: {value.get('name', 'Unknown')} \nOrigin: {value.get('origin', 'Unknown')} \nTaste: {value.get('tasteDescription', 'Unknown')} \nCaffeine: {value.get('caffeine', 'Unknown')}"
                        )
                    except AttributeError:
                        print(f"{key}: {value}")


def main():
    """
    The main entry point of the application that interacts with the user to provide tea recommendations,
    comparisons, and visualizations.

    Returns:
        None
    """
    print("Welcome to the Optimal Steep\n")

    tea_types = TeaTypes()
    tea_types.readFile("teadata.json")

    tea_benefits = TeaBenefits()
    tea_benefits.readFile("teabenefits.csv")

    graph = MyGraph()
    graph.build_graph(tea_types.tea_data, tea_benefits.benefits_data)

    

    while True:
        print()
        try:
            user_choice = int(input("""Please select an option: 
            1. Find tea for a single health concern
            2. Find the best tea for two health concerns
            3. Find & visualize the shortest path between two teas
            4. Discover new teas
            5. Explore teas by characteristic (taste, origin, caffeine)
            6. Compare two teas (e.g., caffeine, taste)
            7. Visualize the shortest path between a health concern and a tea
            8. Visualize the full tea network
            9. Exit
            Your choice: """))

            if user_choice > 9 or user_choice < 1:
                print("Invalid. Please input an integer 1-8, or 9 to exit: ")
                continue

            if user_choice == 1:
                print("Alright! Let's find you tea based on your concerns. \n")
                health_concern = input("Enter a health concern: ")
                graph.recommend_tea_for_health(health_concern)


            elif user_choice == 2:
                print("Great! Please input 2 different health concerns.")
                concern_one = input("Health Concern One: ")
                concern_two = input("Heatlh Concern Two: ")

                while True:
                    flavor_option = input("Do you want to include a flavor preference? Y/N: ")
                    if flavor_option == "Y".lower():
                        flavor = input("Input a flavor preference: ")
                        graph.find_teas([concern_one, concern_two], flavor)
                        break

                    elif flavor_option == "N".lower():
                        flavor = ""
                        graph.find_teas([concern_one, concern_two], flavor)
                        break

                    else:
                        print("Invalid selection. Please select Y or N")

            elif user_choice == 3:
                print("Establish the shortest path between 2 teas based on a health concern: ")
                tea_one = input('Select one tea: ')
                tea_two = input('Select second tea: ')
                health_concern = input('Enter your health concern: ')
                graph.find_shortest_paths(health_concern, [tea_one, tea_two])

                visualize = input('Do you want to see a visualization of this path? Y/N: ')
                if visualize == 'Y'.lower():
                    graph.visualize_shortest_path(tea_one, tea_two)

            elif user_choice == 4:
                print("Here's a list of all of our available teas. ")
                graph.list_all_teas()

            elif user_choice == 5:
                print("Explore teas by a given characteristic! Select a characteristic")
                characteristic = input('Select a characteristic: ')
                matching_teas = graph.explore_tea_by_characteristic(characteristic)
                
                if matching_teas:
                    print(f"Teas matching '{characteristic}':")
                    for tea in matching_teas:
                        print(f"- {tea.title()}")
                else:
                    print(f"No teas found for characteristic '{characteristic}'.")
           
            elif user_choice == 6:
                print("Compare 2 teas based on a given characteristic: ")
                tea_one = input('First tea: ')
                tea_two = input('Second tea: ')
                characteristic = input('Select a comparison characteristic: ')
                graph.compare_teas(tea_one, tea_two, characteristic)   

            elif user_choice == 7:
                health_concern_input = input('Enter a health concern: ')
                tea_target_input = input('Enter a tea: ')

                health_concern_node = graph.find_closest_node(health_concern_input)
                tea_target_node = graph.find_closest_tea_node(tea_target_input)

                if health_concern_node and tea_target_node:
                    graph.visualize_shortest_path_between_teas(health_concern_node, tea_target_node)
                else:
                    print("Could not find matching nodes for the given health concern or tea.")
                
            elif user_choice == 8:
                print("\nVisualizing the full tea network...")
                graph.visualize_graph()

            elif user_choice == 9:
                print("\nThanks for trying The Optimal Steep! Take care :)")
                break
        
        except ValueError:
            print('Invalid. Please enter an integer 1-8, or 9 to exit: ')

if __name__ == "__main__":
    main()
