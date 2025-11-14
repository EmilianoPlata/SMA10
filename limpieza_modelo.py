import mesa
from mesa.discrete_space import CellAgent, OrthogonalMooreGrid
from mesa.visualization import SolaraViz, SpaceRenderer, make_plot_component
from mesa.visualization.components import AgentPortrayalStyle


def compute_percent_clean(model):
    total_cells = len(model.grid.all_cells.cells)
    dirty_agents = [a for a in model.agents if isinstance(a, DirtyAgent)]
    return 100 * (1 - len(dirty_agents) / total_cells)


def compute_total_moves(model):
    cleaning_agents = [a for a in model.agents if isinstance(a, CleaningAgent)]
    return sum(agent.moves for agent in cleaning_agents)


class DirtyAgent(CellAgent):
    """Representa suciedad en una celda."""
    def __init__(self, model, cell):
        super().__init__(model)
        self.cell = cell
        cell.add_agent(self) 


class CleaningAgent(CellAgent):
    def __init__(self, model, cell):
        super().__init__(model)
        self.cell = cell
        cell.add_agent(self)
        self.moves = 0

    def move(self):
        new_cell = self.cell.neighborhood.select_random_cell()
        if new_cell:
            # mover correctamente
            self.cell.remove_agent(self)
            new_cell.add_agent(self)
            self.cell = new_cell
            self.moves += 1

    def step(self):
        contents = list(self.cell.agents)
        dirt = [a for a in contents if isinstance(a, DirtyAgent)]

        if dirt:
            for d in dirt:
                self.cell.remove_agent(d)
                if d in self.model.agents:
                    self.model.agents.remove(d)
        else:
            self.move()


class CleaningModel(mesa.Model):

    def __init__(self, n, width, height, dirty_percent, max_steps, seed=None):
        super().__init__(seed=seed)

        self.num_agents = n
        self.max_steps = max_steps

        self.grid = OrthogonalMooreGrid((width, height), random=self.random)

        cells = list(self.grid.all_cells.cells)

        num_dirty = int(len(cells) * dirty_percent / 100)
        dirty_cells = self.random.sample(cells, num_dirty)

        for cell in dirty_cells:
            DirtyAgent(self, cell)

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

        if compute_percent_clean(self) == 100:
            return

        self.agents.shuffle_do("step")
        self.datacollector.collect(self)
        self.current_step += 1


def agent_portrayal(agent):
    if isinstance(agent, CleaningAgent):
        return AgentPortrayalStyle(color="tab:blue", size=50)
    elif isinstance(agent, DirtyAgent):
        return AgentPortrayalStyle(color="brown", size=15)


model_params = {
    "n": {"type": "SliderInt", "value": 5, "label": "Number of agents:", "min": 1, "max": 50, "step": 1},
    "width": {"type": "SliderInt", "value": 10, "label": "Width:", "min": 1, "max": 50, "step": 1},
    "height": {"type": "SliderInt", "value": 10, "label": "Height:", "min": 1, "max": 50, "step": 1},
    "dirty_percent": {"type": "SliderInt", "value": 100, "label": "Initial Dirty (%)", "min": 0, "max": 100, "step": 5},
    "max_steps": 200,
}

PercentPlot = make_plot_component("PercentClean", page=0)
MovesPlot = make_plot_component("TotalMoves", page=0)

cleaning_model = CleaningModel(n=5, width=10, height=10, dirty_percent=100, max_steps=200)

renderer = SpaceRenderer(model=cleaning_model, backend="matplotlib").render(
    agent_portrayal=agent_portrayal,
)

page = SolaraViz(
    cleaning_model,
    renderer,
    components=[PercentPlot, MovesPlot],
    model_params=model_params,
    name="Reactive Cleaning Robots",
    autoStep = True,
)

app = page
