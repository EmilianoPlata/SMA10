"""
Este codigo se usa para simular agentes de limpieza reactivos que se mueven en una cuadricula para limpiar celdas sucias. 
Los agentes o robots, se mueven aleatoriamente hasta encontrar la suciedad, la limpian y se vuelven a mover hasta limpiar
el 100% del area o si alcanzan el limite de paso establecidos. 

Maria Fernanda Pineda Pat a01752828
Daiana Andrea Armenta Maya A01751408
Emiliano Plata Cardona A01752759

Fecha de creacion: 14/11/25
Fecha de modificacion: 14/11/25
"""

import mesa
from mesa.discrete_space import CellAgent, OrthogonalMooreGrid
from mesa.visualization import SolaraViz, SpaceRenderer, make_plot_component
from mesa.visualization.components import AgentPortrayalStyle


def compute_percent_clean(model):

    """
    Calcula el porcentaje de celdas limpias
    Parámetros: model, instancia del modelo de limpieza
    Regresa: float, porcentaje de celdas limpias (0-100)
    """


    total_cells = len(model.grid.all_cells.cells)
    dirty_agents = [a for a in model.agents if isinstance(a, DirtyAgent)]
    return 100 * (1 - len(dirty_agents) / total_cells)


def compute_total_moves(model):


    """
    Calcula el total de movimientos realizados por todos los agentes de limpieza
    Parámetros: model, instancia del modelo de limpieza
    Regresa: int, suma total de movimientos de todos los robots
    """


    cleaning_agents = [a for a in model.agents if isinstance(a, CleaningAgent)]
    return sum(agent.moves for agent in cleaning_agents)


class DirtyAgent(CellAgent):
    """Representa suciedad en una celda."""
    def __init__(self, model, cell):
        """
        Inicializa un agente de suciedad en una celda especifica

        Parámetros: 
        model, instancia del modelo de simulacion 
        cell, celda donde se encontrara el agente        
        """

        super().__init__(model)
        self.cell = cell
        cell.add_agent(self) 


class CleaningAgent(CellAgent):

    """Representa un robot de limpieza que se mueve y limpia celdas sucias."""

    def __init__(self, model, cell):

        """
        Inicializa un agente de limpieza en una celda especifica 
        Parámetros:
        model, instancia del modelo de simulación
        cell, celda en donde se encontrara el agente

        """

        super().__init__(model)
        self.cell = cell
        cell.add_agent(self)
        self.moves = 0

    def move(self):

        """
        Mueve el agente a una celda vecina aleatoria y actualiza la posición del agente ademas de subir el contador 
        de movimientos.
        """
        new_cell = self.cell.neighborhood.select_random_cell()
        if new_cell:
            # mover correctamente
            self.cell.remove_agent(self)
            new_cell.add_agent(self)
            self.cell = new_cell
            self.moves += 1

    def step(self):

        """
        Ejecuta un paso de la simulación para este agente. Si hay suciedad en la celda en la que se encuentra, la limpia
        Si no hay suciedad, se mueve a una celda vecina disponible
        """
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

    """Modelo de simulación de robots de limpieza reactivos."""

    def __init__(self, n, width, height, dirty_percent, max_steps, seed=None):

        """
        Inicializa el modelo de simulación con robots y suciedad


        Parámetros:
        n, número de agentes de limpieza
        width, ancho de la cuadricula 
        height, alto de la cuadricula 
        dirty_percent, porcentaje inicial de celdas sucias
        max_steps, número máximo de pasos de la simulacion 
        seed, semilla para generación aleatoria, es opcional

        """

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

        """
        Ejecuta un paso de la simulación 

        Detiene la simulación si se alcanza el máximo de pasos o si todas las celdas estan limpias 
        """

        if self.current_step >= self.max_steps:
            return

        if compute_percent_clean(self) == 100:
            return

        self.agents.shuffle_do("step")
        self.datacollector.collect(self)
        self.current_step += 1


def agent_portrayal(agent):

    """
    Define la representación visual de los agentes

    Parámetros: agent, agente a representar

    Retorna: AgentPortrayalStyle, estilo de visualización del agente
    """
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
