import numpy as np
import mesa
from mesa.discrete_space import CellAgent, OrthogonalMooreGrid
from mesa.visualization import SolaraViz, SpaceRenderer, make_plot_component
from mesa.visualization.components import AgentPortrayalStyle

def compute_percent_clean(model):
    total = len(model.grid.all_cells.cells)
    dirty = sum(model.dirty_map.values())
    return 100 * (1 - dirty / total)


def compute_total_moves(model):
    return sum(agent.moves for agent in model.agents)


class CleaningAgent(CellAgent):
    def __init__(self, model, cell):
        super().__init__(model)
        self.cell = cell
        self.moves = 0

    def move(self):
        new_cell = self.cell.neighborhood.select_random_cell()
        if new_cell:
            self.cell = new_cell
            self.moves += 1

    def step(self):
 
        if self.model.dirty_map[self.cell] == 1:
            self.model.dirty_map[self.cell] = 0
        else:
            self.move()

class CleaningModel(mesa.Model):

    def __init__(self, n=5, width=10, height=10, dirty_percent=100, max_steps=200, seed=None):
        super().__init__(seed=seed)

        self.num_agents = n
        self.max_steps = max_steps

        self.grid = OrthogonalMooreGrid((width, height), random=self.random)

        self.cells_list = list(self.grid.all_cells.cells)
        self.dirty_map = {cell: 0 for cell in self.cells_list}
        num_dirty = int(len(self.cells_list) * dirty_percent / 100)

        dirty_cells = self.random.choices(self.cells_list, k=num_dirty)

        for c in dirty_cells:
            self.dirty_map[c] = 1

        start_cell = self.grid[(0, 0)]

        CleaningAgent.create_agents(
            self,
            self.num_agents,
            [start_cell] * self.num_agents,
        )

        self.datacollector = mesa.DataCollector(
            model_reporters={
                "PercentClean": compute_percent_clean,
                "TotalMoves": compute_total_moves,
            }
        )
        self.datacollector.collect(self)

        self.current_step = 0

    def step(self):
        if self.current_step >= self.max_steps:
            return

        self.agents.shuffle_do("step")

        self.datacollector.collect(self)
        self.current_step += 1


def agent_portrayal(agent):
    return AgentPortrayalStyle(color="tab:blue", size=50)

model_params = {
    "n": {"type": "SliderInt", "value": 5, "label": "Number of agents:", "min": 1, "max": 50, "step": 1},
    "width": 10,
    "height": 10,
    "dirty_percent": {"type": "SliderInt", "value": 100, "label": "Initial Dirty (%)", "min": 0, "max": 100, "step": 5},
    "max_steps": 200,
}

PercentPlot = make_plot_component("PercentClean", page=0)
MovesPlot = make_plot_component("TotalMoves", page=0)

cleaning_model = CleaningModel(n=5, width=10, height=10, dirty_percent=100)

renderer = SpaceRenderer(model=cleaning_model, backend="matplotlib").render(
    agent_portrayal=agent_portrayal,
)

page = SolaraViz(
    cleaning_model,
    renderer,
    components=[PercentPlot, MovesPlot],
    model_params=model_params,
    name="Reactive Cleaning Robots",
)

app = page
