from parsimonious.grammar import Grammar
from parsimonious.nodes import NodeVisitor
from .timedautomata import network_timed_automata

TiGaGrammar = Grammar(
    r"""
    strategy        = in_state_block rules newline
    
    in_state_block  = in_open in_state newline? in_condition newline in_close
    in_state        = "(" location+ ws ") " vars
    in_condition    = "(#" space_del_text+ ")"
    in_open         = "Initial state:" newline
    caveat          = "Note: The 'strategy' is not guaranteed to be a strategy."
    in_close        = caveat newline newline in_text
    in_text         = "Strategy to win:" / "Strategy to avoid losing:"
    
    rules           = rule+
    rule            = rule_open state actions
    rule_open       = newline newline "State:" ws
    actions         = (move / delay)+
    
    state           = "(" location+ ws ") " vars
    vars            = var_state*
    var_state       = var_name "=" int ws
    var_name        = (char "." char) / char
    location        = ws text
    loc_addendum    = ws text ws
    
    delay           = newline? del_open invariants del_close
    del_open        = "While you are in" tab
    del_close       = ", wait."
    
    move            = newline? mv_open invariants mv_close transitions
    mv_open         = "When you are in "
    mv_close        = ","
       
    transitions     = tr_open transition (newline transition)*
    transition      = trans conditions
    tr_open         = ws* "take transition" ws*
    trans           = start to end
    to              = "->"
    start           = text
    end             = text
    
    cond            = ","? ws space_del_text+
    conditions_old  = ws "{" cond+ "}"
    conditions      = ws cond_alt
    cond_alt        = ~"{[A-z0-9\.=><:#\?\+\-! ,'\(\)]*}"i
           
    inv             = "&&"? ws? inv_text ws?
    inv_text        = ~"[A-z0-9\.=><\-\+#']+"i
    invariant       = " || "? "(" inv+ ")"
    invariants      = ("true" / invariant+)
    
    tab             = ~"\t"
    ws              = ~"\s*"i
    newline         = ~"\n"
    text            = ~"[A-z0-9\.&=><:#\?\+']*"i
    char            = ~"[A-z0-9]*"i
    int             = ~"[0-9]+"i
    space_del_text  = ws text
    """
)


class parser(NodeVisitor):
    grammar = TiGaGrammar
    strategy = {}
    variables = tuple()

    def visit_strategy(self, node, visited_children):
        """
        strategy = in_state rules newline

        :param node:
        :param visited_children:
        :return:
        """

        return self

    def visit_rule(self, node, visited_children):
        """
        rule = rule_open state actions
        :param node:
        :param visited_children:
        :return:
        """

        _, state, actions = visited_children
        self.strategy[state] = actions
        # add edges, (start, end,
        # state = {name: child for (name, child) in visited_children if child}
        return

    def visit_actions(self, node, visited_children):
        """
        actions = (move / delay)+
        :param node:
        :param visited_children:
        :return:
        """

        return [(x, y) for act in visited_children for x,y in act[0]]

    def visit_location(self, node, visited_children):
        """
        location =  ws text+
        :param node:
        :param visited_children:
        :return:
        """
        ws, text = visited_children
        if len(text) > 0:
            return "".join(text)

    def visit_var_name(self, node, visited_children):
        """
        var_name = char "." char
        """

        return node.text

    def visit_var_state(self, node, visited_children):
        """
        var_state = var_name "=" int ws
        """
        var, _, value, _ = visited_children
        return {var: value}

    def visit_vars(self, node, visited_children):
        """
        vars = var_state*
        """

        var_list = visited_children
        return {n: v for x in var_list for n, v in x.items()}

    def visit_in_state(self, node, visited_children):
        """
        in_state = "(" location+ ws ") " vars
        :param node:
        :param visited_children:
        :return:
        """

        # Just store the variable states and ignore the rest
        _, _, _, _, variables = visited_children
        self.variables = tuple(v for v in variables)
        return

    def visit_state(self, node, visited_children):
        """
        state = "(" location+ ws ") " vars
        :param node:
        :param visited_children:
        :return:
        """
        _, locations, _, _, variables = visited_children
        return tuple(location for location in locations if location) \
            + tuple(variables.values())  # Order is always the same

    def visit_invariant(self, node, visited_children):
        """
        invariant = " || "? "(" inv+ ")"
        :param node:
        :param visited_children:
        :return:
        """
        _, _, invs, _ = visited_children
        return frozenset(inv for inv in invs if len(inv) > 0)

    def visit_inv(self, node, visited_children):
        """
        inv = "&&"? ws? inv_text+ ws?

        Returns
        -------
        List of invariants

        """
        _, _, inv, _ = visited_children
        return inv

    def visit_move(self, node, visited_children):
        """
        move = newline* mv_open invariants mv_close transitions
        :param node:
        :param visited_children:
        :return:
        """
        _, _, invariants, close, transitions = visited_children
        return [(inv, [t[1] for t in transitions]) for inv in invariants]

    def visit_delay(self, node, visited_children):
        """
        delay = newline* del_open invariants del_close
        :param node:
        :param visited_children:
        :return:
        """
        _, _, invariants, _ = visited_children
        return [(inv, "wait") for inv in invariants]

    def visit_transitions(self, node, visited_children):
        """
        transitions = tr_open transition (newline transition)*
        """
        _, first_transition, rest = visited_children
        transitions = [first_transition]
        transitions += [t[1] for t in rest]
        return transitions

    def visit_transition(self, node, visited_children):
        """
        transition = trans conditions
        :param node:
        :param visited_children:
        :return:
        """
        trans, conditions = visited_children
        return trans

    def visit_trans(self, node, visited_children):
        """
        trans = start to end
        :param node:
        :param visited_children:
        :return:
        """
        start, _, end = visited_children
        return start, end

    def visit_start(self, node, *args):
        """
        start = text+
        :param node:
        :param visited_children:
        :return:
        """
        return node.text

    def visit_end(self, node, *args):
        """
        end = text+
        :param node:
        :param visited_children:
        :return:
        """
        return node.text

    def visit_text(self, node, *args):
        return node.text

    def visit_inv_text(self, node, *args):
        return node.text

    def visit_int(self, node, *args):
        return int(node.text)

    def visit_space_del_text(self, node, *args):
        """
        space_del_text = ws* text+
        :param node:
        :param visited_children:
        :return:
        """
        return node.text

    def generic_visit(self, node, visited_children):
        # print(f'skipping {node.expr_name}')
        return visited_children