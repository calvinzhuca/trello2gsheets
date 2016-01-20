Data structure on the output of the TrelloCollector

:output_metadata:
  :report_name: "Name"
  :trello_sources:
    :assignments:
      board1:
        :board_id: "ID"
        :board_name: "name"
        :lists:
          list1:
            :list_id: "ID"
            :list_name: "name"
          list2:
            :list_id: "ID2"
            :list_name: "listname2"
    :epics:
      board2:
        :board_id: "ID"
        :board_name: "name"
        :lists:
          list3:
            :list_id: "id"
            :list_name: "name"
  :collection_datetime: "datetime"
:collected_content:
  ID1:
    :name: "name"
    :id: "trello_id"
    :members: [("Memebers", user_id), ("member2", user_id2)]
    :last_updated: ""
    :detailed_status: ""
    :short_url: ""
    :board_name: ""
    :list_name: ""
    :last_move: ""
    :due_date: ""
    :labels: ["l1", "l2"]
    :desc: ""
    :card_type: "assignment|project|epic"
  ID2:
    :name:
    ...
